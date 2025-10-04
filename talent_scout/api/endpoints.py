from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from services.jd_service import create_job_folder
from services.resume_service import enqueue_resume_processing, get_sorted_candidates
from modelss.schemas import JDCreateResponse, CandidateListResponse

router = APIRouter()

@router.post("/jobs/", response_model=JDCreateResponse)
async def create_job(jd_file: UploadFile = File(...), job_id: str = Form(...)):
    await create_job_folder(jd_file, job_id)
    return JDCreateResponse(job_id=job_id)

@router.post("/jobs/{job_id}/candidates/", status_code=202)
async def upload_candidate_resume(
    background_tasks: BackgroundTasks,
    job_id: str,
    candidate_name: str = Form(...),
    resume_file: UploadFile = File(...)
):
    # Validate job exists
    from services.jd_service import job_exists
    if not job_exists(job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    # Enqueue background processing
    background_tasks.add_task(enqueue_resume_processing, job_id, candidate_name, resume_file)
    return {"message": "Resume received. Processing in background."}

@router.get("/jobs/{job_id}/candidates/", response_model=CandidateListResponse)
async def get_candidates(job_id: str):
    return await get_sorted_candidates(job_id)