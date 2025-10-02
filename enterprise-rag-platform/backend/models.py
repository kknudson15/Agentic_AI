from pydantic import BaseModel
from typing import List, Dict

class IngestResponse(BaseModel):
    status: str
    file: str

class QueryRequest(BaseModel):
    query: str
    session_id: str   # NEW

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict]

class FeedbackRequest(BaseModel):
    query: str
    answer: str
    is_helpful: bool
    sources: List[Dict]
    session_id: str