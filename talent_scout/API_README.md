# Getting Started

## 1. Install Dependencies

Make sure you have Python 3.10+ and pip installed. Then, from the project root:

```bash
pip install -r requirements.txt
```

## 2. Start the FastAPI Server

From the project root (where `main.py` is located):

```bash
uvicorn main:app --reload
```

If port 8000 is busy, use another port:

```bash
uvicorn main:app --reload --port 8001
```

The API docs will be available at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## 3. Environment Variables

- Create a `.env` file in the project root.
- Add your Gemini API key:

```
GEMINI_API_KEY=your_gemini_api_key_here
```

## 4. Project Structure

- `main.py` — FastAPI entry point
- `api/` — API route definitions
- `services/` — Business logic (resume processing, scoring, etc.)
- `models/` — Pydantic schemas for request/response
- `utils/` — File and PDF utilities
- `file_parser.py` — OCR and LLM-based resume parsing
- `prompts.py` — Prompt templates for LLM
- `data/jobs/` — All job and candidate data stored here

## 5. Notes

- All file uploads must use `multipart/form-data`.
- Candidate processing is asynchronous; check the candidates list after a short delay.
- The codebase uses Google Gemini for LLM parsing and scoring.
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
Creates a new job by uploading a Job Description PDF. This creates a folder for the job and saves the JD as `job_description.pdf`.

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
Uploads a candidate’s resume PDF for a specific job. Triggers background processing (OCR, LLM parsing, scoring, question generation).

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
Returns a list of all candidates for the given job, sorted by score, including detailed breakdowns and generated questions.

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
      "score": 79.17,
      "score_breakdown": { ... },
      "rationale": "...",
      "questions": [ ... ]
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
