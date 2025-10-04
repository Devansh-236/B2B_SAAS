# /hr_automation_project/agents/talent_scout/scout_agent.py

import google.generativeai as genai
from talent_scout.prompts import (
    create_resume_parsing_prompt,
    create_scoring_prompt,
    create_interview_question_prompt
)
from core.utils.file_parser import read_pdf_file # Assumes your secure parser is here
import json
import os

class TalentScoutAgent:
    """
    The TalentScoutAgent securely parses resumes, scores them against a job brief,
    and generates a shortlist of top candidates by directly interacting with the Gemini API.
    """
    def __init__(self, api_key: str, model_name: str = 'gemini-pro'):
        """
        Initializes the TalentScoutAgent and configures the Gemini API.

        Args:
            api_key (str): The Google API key for the Gemini service.
            model_name (str): The specific model to use (e.g., 'gemini-pro').
        """
        if not api_key:
            raise ValueError("Gemini API key is required for TalentScoutAgent.")
        
        # --- Direct Gemini API Configuration ---
        genai.configure(api_key=api_key)
        try:
            self.model = genai.GenerativeModel(model_name)
            print(f"Successfully initialized Gemini model '{model_name}' for Talent Scout.")
        except Exception as e:
            print(f"Error initializing Gemini model: {e}")
            raise
        # -----------------------------------------

    def _call_gemini_api(self, prompt: str) -> str:
        """
        A private method to send a prompt to the Gemini API and get the text response.
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"An error occurred during the Gemini API call: {e}")
            return ""

    def _parse_llm_json_response(self, response_text: str, context: str) -> dict or None:
        """A helper function to safely parse JSON from the LLM's text response."""
        if not response_text:
            print(f"LLM returned an empty response for {context}.")
            return None
        
        # Clean the response by removing markdown code fences
        cleaned_text = response_text.strip().replace('```json', '').replace('```', '').strip()
        
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from LLM response for {context}.")
            print(f"Raw response was: {cleaned_text}")
            return None

    def parse_resume_to_json(self, resume_text: str) -> dict:
        """Parses the raw text of a resume into a canonicalized JSON format."""
        prompt = create_resume_parsing_prompt(resume_text)
        response_text = self._call_gemini_api(prompt)
        return self._parse_llm_json_response(response_text, "resume parsing")

    def compute_match_score(self, job_brief: dict, resume_json: dict) -> dict:
        """Computes a match score for a resume against a job brief."""
        prompt = create_scoring_prompt(job_brief, resume_json)
        response_text = self._call_gemini_api(prompt)
        return self._parse_llm_json_response(response_text, "scoring")

    def generate_interview_questions(self, job_brief: dict, resume_json: dict) -> list:
        """Generates tailored interview questions for a candidate."""
        prompt = create_interview_question_prompt(job_brief, resume_json)
        response_text = self._call_gemini_api(prompt)
        response_data = self._parse_llm_json_response(response_text, "question generation")
        return response_data.get("questions", []) if response_data else []

    def screen_resumes(self, job_brief: dict, resume_files: list, max_shortlist_size: int) -> list:
        """Orchestrates the entire resume screening process."""
        candidates = []
        for resume_path in resume_files:
            print(f"Processing resume: {os.path.basename(resume_path)}")
            resume_text = read_pdf_file(resume_path) # Using the secure OCR parser
            if not resume_text:
                print(f"  - Could not extract text from {os.path.basename(resume_path)}. Skipping.")
                continue

            parsed_resume = self.parse_resume_to_json(resume_text)
            if not parsed_resume:
                print(f"  - Failed to parse resume from {os.path.basename(resume_path)}. Skipping.")
                continue

            scores = self.compute_match_score(job_brief, parsed_resume)
            if not scores:
                print(f"  - Failed to score resume for {os.path.basename(resume_path)}. Skipping.")
                continue

            candidate_profile = {
                "resume_file": os.path.basename(resume_path),
                "parsed_data": parsed_resume,
                "match_scores": scores
            }
            candidates.append(candidate_profile)

        # Sort candidates by absolute score
        sorted_candidates = sorted(
            candidates, 
            key=lambda x: x.get('match_scores', {}).get('absolute_score', 0), 
            reverse=True
        )

        # Generate interview questions for the top N candidates
        shortlist = sorted_candidates[:max_shortlist_size]
        for candidate in shortlist:
            questions = self.generate_interview_questions(job_brief, candidate['parsed_data'])
            candidate['recommended_interview_questions'] = questions

        return shortlist

# ==============================================================================
# Example Usage Block (can be moved to main.py)
# ==============================================================================
if __name__ == '__main__':
    # It's best practice to get the API key from an environment variable
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")

    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        print("CRITICAL: Please set your GEMINI_API_KEY in an environment variable or directly in the code.")
    else:
        # 1. Initialize the agent directly
        scout = TalentScoutAgent(api_key=GEMINI_API_KEY)

        # 2. Define the job brief
        job_brief_example = {
            "title": "Senior Python Developer",
            "required_skills": {
                "must_have": ["Python", "Django", "REST APIs", "PostgreSQL", "Unit Testing"],
                "optional": ["React", "Docker", "AWS", "CI/CD"]
            },
            "experience_years": 5
        }

        # 3. List of resumes (ensure these files exist)
        resume_files_list = ["data/input_resumes/sample_resume.pdf"] 

        # 4. Run the screening process
        shortlisted_candidates = scout.screen_resumes(
            job_brief=job_brief_example,
            resume_files=resume_files_list,
            max_shortlist_size=1
        )

        # 5. Print the final, structured output
        print("\n--- SCREENING COMPLETE. FINAL SHORTLIST: ---\n")
        print(json.dumps(shortlisted_candidates, indent=2))