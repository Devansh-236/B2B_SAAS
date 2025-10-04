import os
import json
from utils.file_utils import save_upload_file
from file_parser import _secure_pdf_to_text
from prompts import create_resume_parsing_prompt, create_structured_scoring_prompt, create_interview_question_prompt
from google import genai
from dotenv import load_dotenv

load_dotenv()
DATA_DIR = "data/jobs"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

async def enqueue_resume_processing(job_id, candidate_name, resume_file):
    job_dir = os.path.join(DATA_DIR, job_id)
    resume_path = os.path.join(job_dir, f"{candidate_name}.pdf")
    await save_upload_file(resume_file, resume_path)

    # OCR + LLM parse resume
    resume_text = _secure_pdf_to_text(resume_path)
    resume_prompt = create_resume_parsing_prompt(resume_text)
    resume_response = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=resume_prompt
    )
    resume_json = json.loads(resume_response.text.strip().replace('```json', '').replace('```', '').strip())

    # Parse JD PDF
    jd_path = os.path.join(job_dir, "job_description.pdf")
    jd_text = _secure_pdf_to_text(jd_path)

    # LLM scoring
    scoring_prompt = create_structured_scoring_prompt(jd_text, resume_json)
    scoring_response = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=scoring_prompt
    )
    analysis = json.loads(scoring_response.text.strip().replace('```json', '').replace('```', '').strip())

    # Deterministic scoring (from scout_agent.py)
    scores = _calculate_deterministic_score(analysis, resume_json)

    # Generate interview questions
    job_brief = {
        "title": job_id,
        "required_skills": {
            "must_have": analysis.get("requirements_analysis", {}).get("must_have_skills_from_jd", [])
        }
    }
    question_prompt = create_interview_question_prompt(job_brief, resume_json)
    question_response = gemini_client.models.generate_content(
        model="gemini-2.5-flash",
        contents=question_prompt
    )
    questions = json.loads(question_response.text.strip().replace('```json', '').replace('```', '').strip())["questions"]

    # Save comprehensive candidate JSON
    candidate_json = {
        "candidate_name": candidate_name,
        "resume_text": resume_text,
        "resume_json": resume_json,
        "score": scores.get('total_score'),
        "score_breakdown": scores,
        "questions": questions,
        "rationale": analysis.get("summary_rationale", "N/A")
    }
    candidate_json_path = os.path.join(job_dir, f"{candidate_name}.json")
    with open(candidate_json_path, "w") as f:
        json.dump(candidate_json, f, indent=2)

async def get_sorted_candidates(job_id):
    job_dir = os.path.join(DATA_DIR, job_id)
    candidates = []
    for fname in os.listdir(job_dir):
        if fname.endswith(".json"):
            with open(os.path.join(job_dir, fname), "r") as f:
                data = json.load(f)
                candidates.append({
                    "candidate_name": data["candidate_name"],
                    "score": data["score"],
                    "score_breakdown": data.get("score_breakdown", {}),
                    "rationale": data.get("rationale", "N/A"),
                    "questions": data.get("questions", [])
                })
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return {"candidates": candidates}

def _calculate_deterministic_score(analysis: dict, candidate_data: dict) -> dict:
    # (Copy the logic from scout_agent.py)
    scores = {}
    req = analysis.get("requirements_analysis", {})
    eval = analysis.get("candidate_evaluation", {})

    total_must = len(req.get("must_have_skills_from_jd", []))
    found_must = len(eval.get("found_must_have_skills", []))
    scores['must_have_skills'] = ((found_must / total_must) * 40) if total_must > 0 else 40

    relevance_score = eval.get("experience_relevance_score", 0)
    scores['experience_relevance'] = (relevance_score / 10) * 25

    total_opt = len(req.get("optional_skills_from_jd", []))
    found_opt = len(eval.get("found_optional_skills", []))
    scores['optional_skills'] = ((found_opt / total_opt) * 15) if total_opt > 0 else 15

    req_years = req.get("required_years_experience", 0)
    cand_years = candidate_data.get("experience_years", 0)
    scores['years_of_experience'] = 10 if cand_years >= req_years else 0

    edu_score = eval.get("education_relevance_score", 0)
    scores['education_relevance'] = (edu_score / 10) * 10

    total_score = sum(scores.values())
    scores_rounded = {k: round(v, 2) for k, v in scores.items()}
    scores_rounded['total_score'] = round(total_score, 2)
    return scores_rounded