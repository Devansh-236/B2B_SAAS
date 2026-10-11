from pydantic import BaseModel
from typing import List, Dict, Optional

class JDCreateResponse(BaseModel):
    job_id: str

class CandidateListItem(BaseModel):
    candidate_name: str
    status: str = "completed"
    error: Optional[str] = None
    score: Optional[float] = None
    score_breakdown: Dict[str, float] = {}
    rationale: str = ""
    questions: List[str] = []

class CandidateListResponse(BaseModel):
    candidates: List[CandidateListItem]
