import json

def create_resume_parsing_prompt(resume_text):
    """Used by the file_parser.py to structure raw resume text."""
    return f"""
    You are an expert HR assistant. Your task is to parse the following resume text and extract the key information into a structured JSON format.

    Please extract the following fields:
    - "name": The full name of the candidate.
    - "email": The primary email address.
    - "skills": A list of key technical and soft skills.
    - "experience_years": An integer representing the total years of professional experience.
    - "seniority": An estimated seniority level (e.g., "Junior", "Mid-Level", "Senior").
    - "education": A list of dictionaries, each containing "degree" and "institution".

    Here is the resume text:
    ---
    {resume_text}
    ---

    Please provide the output ONLY in JSON format.
    """

def create_structured_scoring_prompt(job_description_text: str, candidate_json: dict) -> str:
    """
    Creates a prompt that asks the LLM to perform a structured analysis.
    This prompt is the input for the agent's deterministic scoring formula.
    """
    return f"""
    You are a Senior Technical Recruiter performing a detailed candidate-to-job analysis. Your task is to break down the job description, compare it to the candidate's structured resume, and provide a structured JSON analysis. Do not calculate a final score yourself.

    **Step 1: Analyze the Job Description**
    Read the following job description and extract the key requirements.
    ---
    **Job Description:**
    {job_description_text}
    ---

    **Step 2: Analyze the Candidate's Resume**
    Here is the structured data from the candidate's resume.
    ---
    **Candidate JSON:**
    {json.dumps(candidate_json, indent=2)}
    ---

    **Step 3: Provide Structured Analysis**
    Based on your analysis, fill out the following JSON object.
    - `must_have_skills_from_jd` and `optional_skills_from_jd`: list the skills you identified in the JD.
    - `found_must_have_skills` and `found_optional_skills`: list only the skills present in BOTH the JD and the candidate's resume.
    - `experience_relevance_score`: provide an integer score from 0 to 10 on how relevant the candidate's experience is to the role.
    - `education_relevance_score`: provide an integer score from 0 to 10 based on how relevant their education is.
    - `summary_rationale`: write a concise, 2-sentence summary explaining the candidate's fit.

    **Provide your output ONLY in the following JSON format:**
    {{
      "requirements_analysis": {{
        "must_have_skills_from_jd": ["Python", "FastAPI", "LangChain", "GCP"],
        "optional_skills_from_jd": ["Docker", "Kubernetes"],
        "required_years_experience": 3
      }},
      "candidate_evaluation": {{
        "found_must_have_skills": ["Python", "FastAPI", "LangChain"],
        "found_optional_skills": ["Docker"],
        "experience_relevance_score": 9,
        "education_relevance_score": 8
      }},
      "summary_rationale": "The candidate strongly aligns with core technical requirements in Python and LLM frameworks. While they lack GCP experience, their project work is highly relevant."
    }}
    """

def create_interview_question_prompt(job_brief, resume_json):
    """
    Creates a prompt to generate interview questions based on the candidate's profile
    and the job requirements.
    """
    return f"""
    You are a hiring manager preparing for an interview. Your task is to generate 3-5 insightful interview questions for a candidate based on their resume and the job role.

    The questions should be tailored to probe their skills and experience in relation to the job's needs.

    Here is the job brief:
    ---
    Title: {job_brief.get('title')}
    Must-Have Skills: {', '.join(job_brief.get('required_skills', {}).get('must_have', []))}
    ---

    Here is the candidate's parsed resume data:
    ---
    {json.dumps(resume_json, indent=2)}
    ---

    Please generate a list of 3-5 questions. The output should be a JSON object with a single key "questions" that contains a list of strings.

    Example output format:
    {{
      "questions": [
        "Can you describe a challenging project where you used Django and how you overcame the obstacles?",
        "How have you used REST APIs in your previous roles to integrate different systems?",
        "Given your experience with PostgreSQL, can you explain a time you had to optimize a complex query?"
      ]
    }}

    Provide your questions ONLY in the JSON format described above.
    """