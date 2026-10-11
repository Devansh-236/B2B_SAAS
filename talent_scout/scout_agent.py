from prompts import create_structured_scoring_prompt
from scoring import calculate_deterministic_score
from config import BASE_DIR, GEMINI_MODEL
from utils.llm_utils import generate_json
import json
import os
from google import genai

class TalentScoutAgent:
    """
    Ranks candidates using a weighted, deterministic scoring formula. It uses
    the Gemini Client to perform structured analysis, then applies a weighted
    calculation to generate a final, explainable score.
    """
    def __init__(self, api_key: str, model_name: str = GEMINI_MODEL):
        if not api_key:
            raise ValueError("Gemini API key is required.")
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        print(f"Gemini Client initialized for model '{self.model_name}'.")

    def _get_structured_analysis(self, jd_text: str, candidate_data: dict) -> dict:
        """Calls the LLM to get the structured analysis of a candidate."""
        try:
            prompt = create_structured_scoring_prompt(jd_text, candidate_data)
            analysis = generate_json(prompt, client=self.client, model=self.model_name)
            if not isinstance(analysis, dict):
                raise ValueError("LLM response is not a JSON object.")
            return analysis
        except Exception as e:
            name = candidate_data.get('name', 'N/A')
            print(f"  - LLM analysis failed for candidate {name}: {e}")
            return None

    def rank_candidates_for_job(self, job_description_path: str, candidate_json_paths: list) -> list:
        """
        Reads a job description, evaluates all candidate JSONs against it,
        and returns a ranked list of candidates with detailed scores.
        """
        print(f"\n--- Ranking Candidates for Job: {os.path.basename(job_description_path)} ---")
        try:
            with open(job_description_path, 'r') as f:
                jd_text = f.read()
        except IOError as e:
            print(f"Error: Could not read job description file: {e}")
            return []

        ranked_candidates = []
        for json_path in candidate_json_paths:
            try:
                with open(json_path, 'r') as f:
                    candidate_data = json.load(f)
                
                print(f"Evaluating candidate: {candidate_data.get('name', 'Unknown')}")
                
                analysis = self._get_structured_analysis(jd_text, candidate_data)
                if not analysis:
                    continue

                scores = calculate_deterministic_score(analysis, candidate_data)

                ranked_candidates.append({
                    "name": candidate_data.get("name"),
                    "final_score": scores.get('total_score'),
                    "score_breakdown": scores,
                    "rationale": analysis.get("summary_rationale", "N/A"),
                })

            except (IOError, json.JSONDecodeError) as e:
                print(f"  - Could not process candidate file {os.path.basename(json_path)}: {e}")
        
        # Sort candidates by final score in descending order
        return sorted(ranked_candidates, key=lambda x: x['final_score'], reverse=True)

# ==============================================================================
# Example Usage Block
# ==============================================================================
if __name__ == '__main__':
    
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    if not GEMINI_API_KEY:
        print("CRITICAL: Please set the GEMINI_API_KEY environment variable.")
    else:
        scout = TalentScoutAgent(api_key=GEMINI_API_KEY)

        JOB_POSTINGS_DIR = str(BASE_DIR / "job_postings")
        CANDIDATE_JSON_DIR = str(BASE_DIR / "output_files")
        target_job_posting = "llm_engineer_jd.txt" 

        job_path = os.path.join(JOB_POSTINGS_DIR, target_job_posting)
        
        candidate_files = [
            os.path.join(CANDIDATE_JSON_DIR, f)
            for f in os.listdir(CANDIDATE_JSON_DIR)
            if f.endswith(".json")
        ]

        if not os.path.exists(job_path):
            print(f"Error: Job posting not found at '{job_path}'.")
        elif not candidate_files:
            print(f"Error: No candidate JSON files found in '{CANDIDATE_JSON_DIR}'.")
        else:
            final_rankings = scout.rank_candidates_for_job(
                job_description_path=job_path,
                candidate_json_paths=candidate_files
            )

            print("\n\n--- FINAL RANKING RESULTS ---")
            print(json.dumps(final_rankings, indent=2))