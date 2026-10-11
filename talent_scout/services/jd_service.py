import logging
import os
import shutil

from config import DATA_DIR
from file_parser import _secure_pdf_to_text
from utils.file_utils import is_valid_identifier, safe_join, save_bytes

logger = logging.getLogger(__name__)

JD_PDF_NAME = "job_description.pdf"
# Cached OCR output of the JD, extracted once at job creation.
JD_TEXT_NAME = "jd.txt"
MIN_TEXT_CHARS = 50


def get_job_dir(job_id: str) -> str:
    if not is_valid_identifier(job_id):
        raise ValueError("Invalid job_id.")
    return safe_join(DATA_DIR, job_id)


def create_job_folder(job_id: str, jd_content: bytes) -> None:
    """
    Creates the job folder, stores the JD PDF and caches its extracted text.
    Raises FileExistsError if the job already exists and ValueError if no
    usable text could be extracted from the JD.
    """
    job_dir = get_job_dir(job_id)
    os.makedirs(DATA_DIR, exist_ok=True)
    os.mkdir(job_dir)  # raises FileExistsError for duplicate jobs
    try:
        jd_path = os.path.join(job_dir, JD_PDF_NAME)
        save_bytes(jd_content, jd_path)
        jd_text = _secure_pdf_to_text(jd_path)
        if not jd_text or len(jd_text.strip()) < MIN_TEXT_CHARS:
            raise ValueError("Could not extract enough text from the job description PDF.")
        with open(os.path.join(job_dir, JD_TEXT_NAME), "w") as f:
            f.write(jd_text)
    except Exception:
        # Don't leave a half-created job behind; the folder was created by this call.
        shutil.rmtree(job_dir, ignore_errors=True)
        raise


def load_jd_text(job_id: str) -> str:
    """Returns the cached JD text, falling back to OCR (and re-caching) if missing."""
    job_dir = get_job_dir(job_id)
    cache_path = os.path.join(job_dir, JD_TEXT_NAME)
    if os.path.isfile(cache_path):
        with open(cache_path, "r") as f:
            return f.read()
    jd_path = os.path.join(job_dir, JD_PDF_NAME)
    if not os.path.isfile(jd_path):
        return ""
    jd_text = _secure_pdf_to_text(jd_path)
    if jd_text and len(jd_text.strip()) >= MIN_TEXT_CHARS:
        try:
            with open(cache_path, "w") as f:
                f.write(jd_text)
        except OSError as e:
            logger.warning("Could not cache JD text for job %s: %s", job_id, e)
    return jd_text


def job_exists(job_id):
    try:
        return os.path.isdir(get_job_dir(job_id))
    except ValueError:
        return False
