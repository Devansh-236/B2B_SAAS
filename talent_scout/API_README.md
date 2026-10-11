# Getting Started

## 1. Install Dependencies

Make sure you have Python 3.9+ and pip installed. Then, from the `talent_scout/` directory:

```bash
pip install -r requirements.txt
```

PDF OCR also needs two system packages on your `PATH`:

- **Poppler** (used by `pdf2image`): `brew install poppler` (macOS) or `apt install poppler-utils` (Debian/Ubuntu)
- **Tesseract** (used by `pytesseract`): `brew install tesseract` (macOS) or `apt install tesseract-ocr` (Debian/Ubuntu)

## 2. Start the FastAPI Server

From the `talent_scout/` directory (where `main.py` is located):

```bash
uvicorn main:app --reload
```

Or from the repository root:

```bash
uvicorn --app-dir talent_scout main:app --reload
```

If port 8000 is busy (for example when PolicyBot is running), use another port:

```bash
uvicorn main:app --reload --port 8002
```

The API docs will be available at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## 3. Environment Variables

Create a `.env` file in `talent_scout/` (or any parent directory). Example:

```
# Required for resume processing
GEMINI_API_KEY=your_gemini_api_key_here

# Optional (defaults shown)
GEMINI_MODEL=gemini-2.5-flash
TALENT_SCOUT_MAX_UPLOAD_MB=10
TALENT_SCOUT_MAX_PDF_PAGES=10
# TALENT_SCOUT_DATA_DIR=/absolute/path/to/jobs   # defaults to talent_scout/data/jobs
```

The server starts without `GEMINI_API_KEY`; resume processing will then fail and the candidate is listed with `status: "failed"` and an error message.

## 4. Project Structure

- `main.py` — FastAPI entry point
- `config.py` — Settings (paths, Gemini model, upload/OCR limits) read from the environment
- `api/` — API route definitions
- `services/` — Business logic (job creation, resume processing)
- `schemas/` — Pydantic schemas for request/response
- `utils/` — File helpers (validation, safe paths) and Gemini client/JSON helpers
- `scoring.py` — Deterministic weighted scoring formula (shared by the API and `scout_agent.py`)
- `file_parser.py` — OCR (`pdf2image` + Tesseract) and a CLI for batch resume parsing
- `scout_agent.py` — `TalentScoutAgent`, a CLI/library for ranking parsed resumes against a JD text file
- `prompts.py` — Prompt templates for LLM
- `data/jobs/` — All job and candidate data stored here (local only, ignored by git because it holds personal data)
- `tests/` — Offline API tests (Gemini and OCR mocked); run `pytest` from `talent_scout/`

Data layout per job (`data/jobs/<job_id>/`):

- `job_description.pdf` — the uploaded JD
- `jd.txt` — JD text extracted once at job creation (re-created via OCR if missing)
- `<candidate_name>.pdf` — uploaded resume
- `<candidate_name>.json` — candidate record with `status` (`processing`, `failed`, `completed`), `error`, score, rationale and questions

## 5. Notes

- All file uploads must use `multipart/form-data`.
- `job_id` and `candidate_name` must be 1-64 characters of letters, digits, `_` or `-` (otherwise `400`). `job_description` is reserved and cannot be used as a candidate name.
- Uploaded files must be PDFs (`.pdf` extension and a `%PDF-` file signature) and at most `TALENT_SCOUT_MAX_UPLOAD_MB` (default 10 MB, otherwise `413`). Only the first `TALENT_SCOUT_MAX_PDF_PAGES` pages (default 10) are OCR'd.
- Candidate processing is asynchronous; check the candidates list after a short delay.
- The codebase uses Google Gemini (JSON mode) for LLM parsing and scoring. Uploaded resume/JD text is passed to the model inside delimiter tags and treated as data, not instructions.
- For PDF OCR, Tesseract and pdf2image are used (see `file_parser.py`).
- All endpoints are available and testable via the interactive docs at `/docs`.

# Talent Scout API Documentation

## Overview
This API allows you to:
- Create a job by uploading a Job Description (PDF)
- Upload candidate resumes (PDF) for a job
- Retrieve a sorted list of candidates for a job, including detailed scoring and generated interview questions

---

## 1. Create Job

**Endpoint:**
```
POST /jobs/
```

**Description:**
Creates a new job by uploading a Job Description PDF. This creates a folder for the job, saves the JD as `job_description.pdf` and caches its extracted text in `jd.txt`.

**Errors:** `400` invalid `job_id` or non-PDF file, `409` job already exists, `413` file too large, `422` no text could be extracted from the JD.

**Request (multipart/form-data):**
- `jd_file`: (file, required) The Job Description PDF
- `job_id`: (string, required) Unique identifier for the job (e.g., `SWE_Google`)

**Example using Swagger UI:**
- Click "Try it out"
- Enter `job_id` (e.g., `SWE_Google`)
- Upload a PDF file for `jd_file`

**Example using curl:**
```bash
curl -X POST "http://127.0.0.1:8000/jobs/" \
  -F "jd_file=@/path/to/job_description.pdf" \
  -F "job_id=SWE_Google"
```

**Response:**
```json
{
  "job_id": "SWE_Google"
}
```

---

## 2. Upload Candidate Resume

**Endpoint:**
```
POST /jobs/{job_id}/candidates/
```

**Description:**
Uploads a candidate’s resume PDF for a specific job. Triggers background processing (OCR, LLM parsing, scoring, question generation). The candidate immediately appears in the candidate list with `status: "processing"`. Uploading again with the same `candidate_name` replaces the previous resume.

**Errors:** `400` invalid `job_id`/`candidate_name` or non-PDF file, `404` job not found, `413` file too large.

**Request (multipart/form-data):**
- `candidate_name`: (string, required) Candidate’s name
- `resume_file`: (file, required) The candidate’s resume PDF

**Example using Swagger UI:**
- Click "Try it out"
- Enter `candidate_name` (e.g., `Parth`)
- Upload a PDF file for `resume_file`
- Enter the `job_id` in the path parameter

**Example using curl:**
```bash
curl -X POST "http://127.0.0.1:8000/jobs/SWE_Google/candidates/" \
  -F "candidate_name=Parth" \
  -F "resume_file=@/path/to/Parth_Resume.pdf"
```

**Response:**
```json
{
  "message": "Resume received. Processing in background."
}
```

---

## 3. Get Sorted Candidates for a Job

**Endpoint:**
```
GET /jobs/{job_id}/candidates/
```

**Description:**
Returns a list of all candidates for the given job, sorted by score (candidates without a score, i.e. still processing or failed, come last), including detailed breakdowns and generated questions.

**Errors:** `400` invalid `job_id`, `404` job not found.

**Request:**
- `job_id`: (string, required, in path) The job identifier

**Example using Swagger UI:**
- Click "Try it out"
- Enter the `job_id` (e.g., `SWE_Google`)

**Example using curl:**
```bash
curl -X GET "http://127.0.0.1:8000/jobs/SWE_Google/candidates/"
```

**Response:**
```json
{
  "candidates": [
    {
      "candidate_name": "dada",
      "status": "completed",
      "error": null,
      "score": 79.17,
      "score_breakdown": { ... },
      "rationale": "...",
      "questions": [ ... ]
    },
    {
      "candidate_name": "Parth",
      "status": "failed",
      "error": "The uploaded resume PDF doesn't seem to be valid. Please upload a valid resume in PDF format only.",
      "score": null,
      "score_breakdown": {},
      "rationale": "N/A",
      "questions": []
    },
    ...
  ]
}
```

---

## How to Pass PDFs in Requests

- **Swagger UI:** Use the file upload button for `jd_file` or `resume_file`.
- **curl:** Use `-F "fieldname=@/path/to/file.pdf"` for file fields.
- **Python requests:**
    ```python
    import requests

    # For job creation
    with open("job_description.pdf", "rb") as f:
        response = requests.post(
            "http://127.0.0.1:8000/jobs/",
            files={"jd_file": f},
            data={"job_id": "SWE_Google"}
        )

    # For resume upload
    with open("Parth_Resume.pdf", "rb") as f:
        response = requests.post(
            "http://127.0.0.1:8000/jobs/SWE_Google/candidates/",
            files={"resume_file": f},
            data={"candidate_name": "Parth"}
        )
    ```

---

## Notes
- All endpoints are available and testable via the interactive docs at `http://127.0.0.1:8000/docs`.
- All file uploads must use `multipart/form-data`.
- Candidate processing is asynchronous; check the candidates list after a short delay.
