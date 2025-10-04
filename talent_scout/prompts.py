def create_resume_parsing_prompt(resume_text):
    """
    Creates a prompt to instruct the LLM to parse a resume's text into a
    structured JSON format.
    """
    return f"""
    You are an expert HR assistant. Your task is to parse the following resume text and extract the key information into a structured JSON format.

    Please extract the following fields:
    - "name": The full name of the candidate.
    - "email": The primary email address.
    - "skills": A list of key technical and soft skills.
    - "experience_years": The total number of years of professional experience. If not explicitly stated, estimate based on the work history.
    - "seniority": An estimated seniority level (e.g., "Junior", "Mid-Level", "Senior", "Lead").
    - "education": A list of dictionaries, where each dictionary contains "degree" and "institution".

    Here is the resume text:
    ---
    {resume_text}
    ---

    Please provide the output ONLY in JSON format, like the example below:
    {{
      "name": "John Doe",
      "email": "john.doe@example.com",
      "skills": ["Python", "Data Analysis", "Machine Learning", "Team Leadership"],
      "experience_years": 8,
      "seniority": "Senior",
      "education": [
        {{
          "degree": "Master of Science in Computer Science",
          "institution": "University of Technology"
        }}
      ]
    }}
    """

def create_scoring_prompt(job_brief, resume_json):
    """
    Creates a prompt for the LLM to score a resume against a job brief.
    """
    return f"""
    You are an expert technical recruiter. Your task is to evaluate a candidate's resume against a job description and provide a match score.

    Here is the job brief:
    ---
    Title: {job_brief.get('title')}
    Must-Have Skills: {', '.join(job_brief.get('required_skills', {}).get('must_have', []))}
    Optional Skills: {', '.join(job_brief.get('required_skills', {}).get('optional', []))}
    Required Experience (years): {job_brief.get('experience_years')}
    ---

    Here is the candidate's parsed resume data:
    ---
    {json.dumps(resume_json, indent=2)}
    ---

    Please provide a score and a rationale in the following JSON format.
    The "absolute_score" should be an integer between 0 and 100, where 100 is a perfect match.
    The "rationale" should be a brief, 2-3 sentence explanation of why you gave this score, highlighting strengths and weaknesses.

    Example output format:
    {{
      "absolute_score": 85,
      "rationale": "The candidate is a strong fit, possessing all must-have skills and the required years of experience. They lack some optional skills like AWS, but their core expertise in Python and Django is excellent."
    }}

    Provide your evaluation ONLY in the JSON format described above.
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