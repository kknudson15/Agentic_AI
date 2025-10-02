# backend/main.py
from fastapi import FastAPI, UploadFile, Request
from fastapi.responses import StreamingResponse
from backend.ingestion import ingest_document
from backend.retriever import query_docs
from backend.hybrid_retriever import query_hybrid
from backend.streaming import stream_sse_with_memory
from backend.models import IngestResponse, QueryRequest, QueryResponse, FeedbackRequest
from backend.feedback import add_feedback
from backend.streaming import stream_sse_with_memory
from backend.mem import router as mem_router, format_sources_for_frontend
from pydantic import BaseModel
import json
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

# Now you can access OPENAI_API_KEY
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = FastAPI()
app.include_router(mem_router)

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.post("/ingest/", response_model=IngestResponse)
async def ingest(file: UploadFile):
    content = await file.read()
    ingest_document(content, file.filename)
    return {"status": "success", "file": file.filename}

@app.post("/query/", response_model=QueryResponse)
async def query(req: QueryRequest):
    answer, sources = query_docs(req.query)
    return {"answer": answer, "sources": sources}

@app.post("/query_hybrid/", response_model=QueryResponse)
async def query_hybrid_endpoint(req: QueryRequest):
    answer, sources = query_hybrid(req.query)
    return {"answer": answer, "sources": sources}

@app.post("/feedback/")
async def feedback(req: FeedbackRequest):
    result = add_feedback(
        query=req.query,
        answer=req.answer,
        is_helpful=req.is_helpful,
        sources=json.dumps(req.sources)
    )
    return result

class ResetMemoryRequest(BaseModel):
    session_id: str

@app.post("/reset_memory/")
async def reset_memory(session_id: str):
    from backend.mem import reset_session
    reset_session(session_id)
    return {"status": "memory cleared"}

@app.post("/query_sse_memory/")
async def query_sse_memory(request: Request):
    data = await request.json()
    question = data.get("question", "")
    session_id = request.headers.get("X-Session-ID") or "default_session"
    k = data.get("k", 3)

    return stream_sse_with_memory(session_id=session_id, question=question, k=k)