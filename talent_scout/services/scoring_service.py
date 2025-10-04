def score_candidate(resume_text, jd_text):
    # Dummy scoring logic
    score = len(set(resume_text.split()) & set(jd_text.split())) / max(1, len(jd_text.split()))
    score_breakdown = {"overlap": score}
    return score, score_breakdown

def generate_questionnaire(resume_text, jd_text):
    # Dummy questions
    return [
        "Why are you a good fit for this role?",
        "Describe your relevant experience."
    ]