from prompts import create_structured_scoring_prompt
import json
import os
from google import genai
from dotenv import load_dotenv
load_dotenv()
class TalentScoutAgent:
    """
    Ranks candidates using a weighted, deterministic scoring formula. It uses
    the Gemini Client to perform structured analysis, then applies a weighted
    calculation to generate a final, explainable score.
    """
    def __init__(self, api_key: str, model_name: str = 'gemini-2.5-flash'):
        if not api_key:
            raise ValueError("Gemini API key is required.")
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name
        print(f"Gemini Client initialized for model '{self.model_name}'.")

    def _get_structured_analysis(self, jd_text: str, candidate_data: dict) -> dict:
        """Calls the LLM to get the structured analysis of a candidate."""
        try:
            prompt = create_structured_scoring_prompt(jd_text, candidate_data)
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            cleaned_text = response.text.strip().replace('```json', '').replace('```', '').strip()
            return json.loads(cleaned_text)
        except Exception as e:
            name = candidate_data.get('name', 'N/A')
            print(f"  - LLM analysis failed for candidate {name}: {e}")
            return None
    def _calculate_deterministic_score(self, analysis: dict, candidate_data: dict) -> dict:
        """
        Applies a weighted formula to the structured analysis from the LLM.
        This ensures consistent and transparent scoring.
        """
        # --- SCORING RUBRIC (Total 100 points) ---
        # 1. Must-Have Skills: 40 points (Most important)
        # 2. Experience Relevance: 25 points (Quality of experience)
        # 3. Optional Skills: 15 points (Differentiator)
        # 4. Years of Experience: 10 points (Binary check)
        # 5. Education Relevance: 10 points (Tie-breaker)
        # ----------------------------------------------------
        
        scores = {}
        req = analysis.get("requirements_analysis", {})
        eval = analysis.get("candidate_evaluation", {})

        # 1. Must-Have Skills Score (Weight: 40)
        total_must = len(req.get("must_have_skills_from_jd", []))
        found_must = len(eval.get("found_must_have_skills", []))
        scores['must_have_skills'] = ((found_must / total_must) * 40) if total_must > 0 else 40

        # 2. Experience Relevance Score (Weight: 25)
        # LLM provides a score from 0-10, we scale it to 25 points.
        relevance_score = eval.get("experience_relevance_score", 0)
        scores['experience_relevance'] = (relevance_score / 10) * 25

        # 3. Optional Skills Score (Weight: 15)
        total_opt = len(req.get("optional_skills_from_jd", []))
        found_opt = len(eval.get("found_optional_skills", []))
        scores['optional_skills'] = ((found_opt / total_opt) * 15) if total_opt > 0 else 15

        # 4. Years of Experience Score (Weight: 10)
        req_years = req.get("required_years_experience", 0)
        cand_years = candidate_data.get("experience_years", 0)
        scores['years_of_experience'] = 10 if cand_years >= req_years else 0

        # 5. Education Relevance Score (Weight: 10)
        # LLM provides a score from 0-10, we scale it to 10 points.
        edu_score = eval.get("education_relevance_score", 0)
        scores['education_relevance'] = (edu_score / 10) * 10
        
        # Calculate Total Score and round all values for cleanliness
        total_score = sum(scores.values())
        scores_rounded = {k: round(v, 2) for k, v in scores.items()}
        scores_rounded['total_score'] = round(total_score, 2)
        
        return scores_rounded

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

                scores = self._calculate_deterministic_score(analysis, candidate_data)

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

        JOB_POSTINGS_DIR = "job_postings"
        CANDIDATE_JSON_DIR = "output_files"
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