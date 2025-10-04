import os
from utils.file_utils import save_upload_file

DATA_DIR = "data/jobs"

async def create_job_folder(jd_file, job_id):
    job_dir = os.path.join(DATA_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    jd_path = os.path.join(job_dir, "job_description.pdf")
    await save_upload_file(jd_file, jd_path)

def job_exists(job_id):
    return os.path.exists(os.path.join(DATA_DIR, job_id))