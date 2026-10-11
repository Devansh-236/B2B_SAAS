from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.concurrency import run_in_threadpool

from config import MAX_UPLOAD_BYTES, MAX_UPLOAD_MB
from services.jd_service import create_job_folder, job_exists
from services.resume_service import (
    get_sorted_candidates,
    is_valid_candidate_name,
    process_resume,
    save_resume,
)
from schemas.schemas import JDCreateResponse, CandidateListResponse
from utils.file_utils import is_pdf_bytes, is_valid_identifier

router = APIRouter()

IDENTIFIER_RULE = "Use 1-64 characters: letters, digits, '_' or '-'."


def _require_valid_job_id(job_id: str) -> None:
    if not is_valid_identifier(job_id):
        raise HTTPException(status_code=400, detail=f"Invalid job_id. {IDENTIFIER_RULE}")


async def _read_pdf_upload(upload: UploadFile) -> bytes:
    """Reads an uploaded file, enforcing the size cap and checking it is a PDF."""
    filename = upload.filename or ""
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF file allowed.")
    content = await upload.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {MAX_UPLOAD_MB:g} MB.")
    # Rely on the file signature rather than the client-supplied content type.
    if not is_pdf_bytes(content):
        raise HTTPException(status_code=400, detail="Only PDF file allowed.")
    return content


@router.post("/jobs/", response_model=JDCreateResponse)
async def create_job(jd_file: UploadFile = File(...), job_id: str = Form(...)):
    _require_valid_job_id(job_id)
    content = await _read_pdf_upload(jd_file)
    try:
        # OCR of the JD is blocking, so keep it off the event loop.
        await run_in_threadpool(create_job_folder, job_id, content)
    except FileExistsError:
        raise HTTPException(status_code=409, detail="Job already exists.")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return JDCreateResponse(job_id=job_id)


@router.post("/jobs/{job_id}/candidates/", status_code=202)
async def upload_candidate_resume(
    background_tasks: BackgroundTasks,
    job_id: str,
    candidate_name: str = Form(...),
    resume_file: UploadFile = File(...)
):
    _require_valid_job_id(job_id)
    if not job_exists(job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    if not is_valid_candidate_name(candidate_name):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid candidate_name. {IDENTIFIER_RULE} 'job_description' is reserved.",
        )
    content = await _read_pdf_upload(resume_file)
    await run_in_threadpool(save_resume, job_id, candidate_name, content)
    # process_resume is a plain function, so it runs in a threadpool after the response.
    background_tasks.add_task(process_resume, job_id, candidate_name)
    return {"message": "Resume received. Processing in background."}


@router.get("/jobs/{job_id}/candidates/", response_model=CandidateListResponse)
def get_candidates(job_id: str):
    _require_valid_job_id(job_id)
    try:
        return get_sorted_candidates(job_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found")
