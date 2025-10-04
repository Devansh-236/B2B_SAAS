from pydantic import BaseModel
from typing import List,Dict,Any

class JDCreateResponse(BaseModel):
    job_id: str

class CandidateListItem(BaseModel):
    candidate_name: str
    score: float
    score_breakdown: Dict[str, float] = {}
    rationale: str = ""
    questions: List[str] = []

class CandidateListResponse(BaseModel):
    candidates: List[CandidateListItem]