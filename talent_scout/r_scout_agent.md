# `scout_agent.py` - The Talent Scout Agent

## Overview

This file contains the `TalentScoutAgent`, a standalone ranker for the resume screening stage of the HR automation system. Given a job description (plain text) and a set of already-parsed candidate JSON files, it scores every candidate against the job and returns a ranked list with an explainable score breakdown.

The FastAPI service (`main.py`, `services/resume_service.py`) uses the same prompts and the same scoring formula, but also handles OCR, resume parsing and interview question generation per uploaded resume.

## How It Works

1.  **Structured analysis (LLM)**: For each candidate, `_get_structured_analysis` sends the JD text and the candidate JSON to Gemini using `create_structured_scoring_prompt` from `prompts.py`. The model runs in JSON mode and returns the JD's must-have/optional skills and required years of experience, the skills the candidate matches, and 0-10 relevance scores for experience and education.

2.  **Deterministic scoring**: `calculate_deterministic_score` (in `scoring.py`) turns that analysis into a score out of 100:
    -   Must-have skills: 40 points (share of JD must-have skills the candidate has)
    -   Experience relevance: 25 points (LLM score 0-10, scaled)
    -   Optional skills: 15 points
    -   Years of experience: 10 points (candidate years >= required years)
    -   Education relevance: 10 points (LLM score 0-10, scaled)

    LLM values are coerced to numbers and clamped, so missing or malformed fields (e.g. `"3+ years"` or `null`) do not crash scoring.

3.  **Ranking**: `rank_candidates_for_job(job_description_path, candidate_json_paths)` reads the JD file, evaluates each candidate, and returns the candidates sorted by `final_score` with their `score_breakdown` and the LLM's `summary_rationale`.

## Dependencies

-   `google-genai`: The Google Gen AI SDK used to call Gemini.
-   `prompts.py`: Prompt templates (`create_structured_scoring_prompt`).
-   `scoring.py`: The shared deterministic scoring formula.
-   `utils/llm_utils.py`: Gemini JSON-mode call and tolerant JSON parsing.
-   `config.py`: Settings such as the `GEMINI_MODEL` (default `gemini-2.5-flash`), read from the environment / `.env`.

Candidate JSON files are produced by `file_parser.py` (`process_resumes_to_json`), which OCRs resume PDFs and parses them with `create_resume_parsing_prompt`.

## Usage

Run from any directory (paths are resolved relative to `talent_scout/`):

```bash
# 1. Parse resumes in resume_files/ into output_files/*.json
python talent_scout/file_parser.py

# 2. Rank them against job_postings/llm_engineer_jd.txt
python talent_scout/scout_agent.py
```

Or use it as a library:

```python
from scout_agent import TalentScoutAgent

scout = TalentScoutAgent(api_key="...")
rankings = scout.rank_candidates_for_job("job_postings/llm_engineer_jd.txt", ["output_files/candidate.json"])
```
