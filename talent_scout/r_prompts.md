# `prompts.py` - Prompts for the Talent Scout Agent

## Overview

This file centralizes all the prompt templates used by the Talent Scout API (`services/resume_service.py`), the `TalentScoutAgent` (`scout_agent.py`) and the batch parser (`file_parser.py`). Separating the prompts from the application logic makes it easier to experiment with and refine them without altering the core code.

## Purpose of Prompts

Prompts are carefully constructed text inputs that guide the behavior of the Large Language Model (LLM). Here they instruct Gemini to perform specific NLP tasks and to return the output as JSON. The calls are made in Gemini's JSON mode (`response_mime_type: application/json`, see `utils/llm_utils.py`), with a tolerant fallback parser.

## Prompts Included

1.  **`create_resume_parsing_prompt(resume_text)`**:
    -   **Goal**: Read the raw (OCR) text of a resume and extract key information.
    -   **Output Format**: A JSON object with `name`, `email`, `skills`, `experience_years`, `seniority`, and `education`. This structured output is used for scoring and question generation.

2.  **`create_structured_scoring_prompt(job_description_text, candidate_json)`**:
    -   **Goal**: Compare a parsed resume with the job description. The LLM does not compute a final score itself.
    -   **Output Format**: A JSON object with `requirements_analysis` (`must_have_skills_from_jd`, `optional_skills_from_jd`, `required_years_experience`), `candidate_evaluation` (`found_must_have_skills`, `found_optional_skills`, `experience_relevance_score` 0-10, `education_relevance_score` 0-10) and `summary_rationale`. The final score is calculated deterministically from this by `calculate_deterministic_score` in `scoring.py`.

3.  **`create_interview_question_prompt(job_brief, resume_json)`**:
    -   **Goal**: Generate 3-5 interview questions based on the candidate's resume and the job's must-have skills.
    -   **Output Format**: A JSON object `{"questions": [...]}` containing a list of strings.

## Handling Untrusted Input

Resume text, JD text and parsed resume JSON come from users and may contain text that tries to steer the model (prompt injection). Instead of redacting content, every prompt:

-   wraps untrusted content in delimiter tags (`<resume>`, `<job_description>`, `<candidate_json>`, `<job_brief>`),
-   tells the model that content inside those tags is data and any instructions inside must be ignored,
-   removes control characters and any copies of the delimiter tags from the content, and caps its length (`MAX_UNTRUSTED_CHARS`).

## Best Practices for Prompt Engineering

-   **Be Specific and Clear**: The prompts are designed to be unambiguous to reduce the chances of the LLM misinterpreting the request.
-   **Define the Output Structure**: Each prompt explicitly asks for JSON with a predefined schema, and includes an example of it.
-   **Validate the Output**: Callers check that the required fields are present and coerce numeric fields, since LLM output is not guaranteed to follow the schema.
