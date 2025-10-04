from fastapi import APIRouter
from pydantic import BaseModel
from backend.app.agents.sql_agent import orchestrate_query

router = APIRouter()

class QueryRequest(BaseModel):
    user_query: str
    execute: bool = False

class QueryResponse(BaseModel):
    sql: str | None = None
    validation: dict | None = None
    execution: dict | None = None

@router.post("/query", response_model=QueryResponse)
def run_query(request: QueryRequest):
    result = orchestrate_query(request.user_query, execute=request.execute)
    return QueryResponse(sql=result.get("sql"), validation=result.get("validation"), execution=result.get("execution"))

