import math
import re

# --- SCORING RUBRIC (Total 100 points) ---
# 1. Must-Have Skills: 40 points (Most important)
# 2. Experience Relevance: 25 points (Quality of experience)
# 3. Optional Skills: 15 points (Differentiator)
# 4. Years of Experience: 10 points (Binary check)
# 5. Education Relevance: 10 points (Tie-breaker)
# ----------------------------------------------------


def _to_number(value, default: float = 0.0) -> float:
    """Coerce LLM output (int, float, "3", "3+ years", None, ...) to a float."""
    if isinstance(value, bool):
        return default
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str):
        match = re.search(r"-?\d+(?:\.\d+)?", value)
        if not match:
            return default
        number = float(match.group())
    else:
        return default
    return number if math.isfinite(number) else default


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _as_dict(value) -> dict:
    return value if isinstance(value, dict) else {}


def _as_list(value) -> list:
    return value if isinstance(value, list) else []


def _ratio(found: list, total: list) -> float:
    if not total:
        return 1.0
    return _clamp(len(found) / len(total), 0.0, 1.0)


def calculate_deterministic_score(analysis: dict, candidate_data: dict) -> dict:
    """
    Applies a weighted formula to the structured analysis from the LLM.
    This ensures consistent and transparent scoring.
    """
    analysis = _as_dict(analysis)
    candidate_data = _as_dict(candidate_data)
    req = _as_dict(analysis.get("requirements_analysis"))
    evaluation = _as_dict(analysis.get("candidate_evaluation"))

    scores = {}

    # 1. Must-Have Skills Score (Weight: 40)
    scores['must_have_skills'] = _ratio(
        _as_list(evaluation.get("found_must_have_skills")),
        _as_list(req.get("must_have_skills_from_jd")),
    ) * 40

    # 2. Experience Relevance Score (Weight: 25)
    # LLM provides a score from 0-10, we scale it to 25 points.
    relevance_score = _clamp(_to_number(evaluation.get("experience_relevance_score")), 0, 10)
    scores['experience_relevance'] = (relevance_score / 10) * 25

    # 3. Optional Skills Score (Weight: 15)
    scores['optional_skills'] = _ratio(
        _as_list(evaluation.get("found_optional_skills")),
        _as_list(req.get("optional_skills_from_jd")),
    ) * 15

    # 4. Years of Experience Score (Weight: 10)
    req_years = _to_number(req.get("required_years_experience"))
    cand_years = _to_number(candidate_data.get("experience_years"))
    scores['years_of_experience'] = 10 if cand_years >= req_years else 0

    # 5. Education Relevance Score (Weight: 10)
    # LLM provides a score from 0-10, we scale it to 10 points.
    edu_score = _clamp(_to_number(evaluation.get("education_relevance_score")), 0, 10)
    scores['education_relevance'] = (edu_score / 10) * 10

    # Calculate Total Score and round all values for cleanliness
    total_score = sum(scores.values())
    scores_rounded = {k: round(v, 2) for k, v in scores.items()}
    scores_rounded['total_score'] = round(total_score, 2)
    return scores_rounded
