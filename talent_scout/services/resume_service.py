import json
import logging
import os

from file_parser import _secure_pdf_to_text
from prompts import create_resume_parsing_prompt, create_structured_scoring_prompt, create_interview_question_prompt
from scoring import calculate_deterministic_score
from services.jd_service import MIN_TEXT_CHARS, get_job_dir, load_jd_text
from utils.file_utils import is_valid_identifier, safe_join, save_bytes, write_json_atomic
from utils.llm_utils import generate_json

logger = logging.getLogger(__name__)

# Names that would collide with job-level files (e.g. job_description.pdf).
RESERVED_CANDIDATE_NAMES = {"job_description"}

STATUS_PROCESSING = "processing"
STATUS_FAILED = "failed"
STATUS_COMPLETED = "completed"

INVALID_RESUME_MESSAGE = "The uploaded resume PDF doesn't seem to be valid. Please upload a valid resume in PDF format only."


class ResumeProcessingError(Exception):
    """Raised for expected processing failures; the message is shown to API users."""


def is_valid_candidate_name(candidate_name) -> bool:
    return (
        is_valid_identifier(candidate_name)
        and candidate_name.lower() not in RESERVED_CANDIDATE_NAMES
    )


def _candidate_paths(job_id: str, candidate_name: str):
    if not is_valid_candidate_name(candidate_name):
        raise ValueError("Invalid candidate_name.")
    job_dir = get_job_dir(job_id)
    return (
        safe_join(job_dir, f"{candidate_name}.pdf"),
        safe_join(job_dir, f"{candidate_name}.json"),
    )


def save_resume(job_id: str, candidate_name: str, content: bytes) -> None:
    """Stores the resume PDF and marks the candidate as processing."""
    resume_path, record_path = _candidate_paths(job_id, candidate_name)
    save_bytes(content, resume_path)
    write_json_atomic(
        {"candidate_name": candidate_name, "status": STATUS_PROCESSING},
        record_path,
    )


def process_resume(job_id: str, candidate_name: str) -> None:
    """
    Background task: OCR + LLM parse the resume, score it against the JD and
    generate interview questions. Always leaves a status record behind.
    Runs as a plain function so Starlette executes it in a threadpool.
    """
    _, record_path = _candidate_paths(job_id, candidate_name)
    try:
        record = _build_candidate_record(job_id, candidate_name)
    except ResumeProcessingError as e:
        logger.warning("Processing failed for %s (job %s): %s", candidate_name, job_id, e)
        record = {"candidate_name": candidate_name, "status": STATUS_FAILED, "error": str(e)}
    except Exception:
        logger.exception("Unexpected error while processing %s (job %s)", candidate_name, job_id)
        record = {
            "candidate_name": candidate_name,
            "status": STATUS_FAILED,
            "error": "Unexpected error while processing the resume.",
        }
    write_json_atomic(record, record_path)


def _build_candidate_record(job_id: str, candidate_name: str) -> dict:
    resume_path, _ = _candidate_paths(job_id, candidate_name)

    # OCR + LLM parse resume
    resume_text = _secure_pdf_to_text(resume_path)
    if not resume_text or len(resume_text.strip()) < MIN_TEXT_CHARS:
        raise ResumeProcessingError(INVALID_RESUME_MESSAGE)

    try:
        resume_json = generate_json(create_resume_parsing_prompt(resume_text))
    except Exception as e:
        raise ResumeProcessingError(f"Resume parsing failed: {e}") from e
    if not isinstance(resume_json, dict) or not resume_json.get("name") or not resume_json.get("skills"):
        raise ResumeProcessingError(INVALID_RESUME_MESSAGE)

    # JD text (cached at job creation, OCR fallback otherwise)
    jd_text = load_jd_text(job_id)
    if not jd_text or len(jd_text.strip()) < MIN_TEXT_CHARS:
        raise ResumeProcessingError("Could not read the job description for this job.")

    # LLM scoring
    try:
        analysis = generate_json(create_structured_scoring_prompt(jd_text, resume_json))
    except Exception as e:
        raise ResumeProcessingError(f"LLM scoring failed: {e}") from e
    if (
        not isinstance(analysis, dict)
        or not isinstance(analysis.get("requirements_analysis"), dict)
        or not isinstance(analysis.get("candidate_evaluation"), dict)
    ):
        raise ResumeProcessingError("Scoring output was missing required fields.")

    # Deterministic scoring
    scores = calculate_deterministic_score(analysis, resume_json)

    # Generate interview questions (optional; failures don't fail the candidate)
    job_brief = {
        "title": job_id,
        "required_skills": {
            "must_have": analysis["requirements_analysis"].get("must_have_skills_from_jd", [])
        }
    }
    questions = []
    try:
        questions_json = generate_json(create_interview_question_prompt(job_brief, resume_json))
        if isinstance(questions_json, dict) and isinstance(questions_json.get("questions"), list):
            questions = [q for q in questions_json["questions"] if isinstance(q, str)]
    except Exception as e:
        logger.warning("LLM question generation failed for %s: %s", candidate_name, e)

    rationale = analysis.get("summary_rationale")
    return {
        "candidate_name": candidate_name,
        "status": STATUS_COMPLETED,
        "resume_text": resume_text,
        "resume_json": resume_json,
        "score": scores.get('total_score'),
        "score_breakdown": scores,
        "questions": questions,
        "rationale": rationale if isinstance(rationale, str) else "N/A",
    }


def _to_float(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def get_sorted_candidates(job_id):
    """
    Lists candidates for a job sorted by score (unscored ones last).
    Raises FileNotFoundError if the job does not exist.
    """
    job_dir = get_job_dir(job_id)
    if not os.path.isdir(job_dir):
        raise FileNotFoundError(job_id)

    candidates = []
    for fname in os.listdir(job_dir):
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(job_dir, fname), "r") as f:
                data = json.load(f)
        except (OSError, ValueError) as e:
            logger.warning("Skipping unreadable candidate file %s: %s", fname, e)
            continue
        if not isinstance(data, dict):
            continue

        score = _to_float(data.get("score"))
        breakdown = data.get("score_breakdown")
        breakdown = breakdown if isinstance(breakdown, dict) else {}
        questions = data.get("questions")
        questions = questions if isinstance(questions, list) else []
        rationale = data.get("rationale")
        error = data.get("error")
        candidate_name = data.get("candidate_name")
        # Records written before status tracking existed are complete if scored.
        status = data.get("status") or (STATUS_COMPLETED if score is not None else STATUS_FAILED)

        candidates.append({
            "candidate_name": candidate_name if isinstance(candidate_name, str) else fname[:-len(".json")],
            "status": str(status),
            "error": error if isinstance(error, str) else None,
            "score": score,
            "score_breakdown": {k: v for k, v in breakdown.items() if _to_float(v) is not None},
            "rationale": rationale if isinstance(rationale, str) else "N/A",
            "questions": [q for q in questions if isinstance(q, str)],
        })
    candidates.sort(key=lambda c: (c["score"] is None, -(c["score"] or 0)))
    return {"candidates": candidates}
