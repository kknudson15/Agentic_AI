from fastapi import APIRouter
from typing import Dict

router = APIRouter()

# Simple in-memory store for demonstration
memory_store: Dict[str, list] = {}  # session_id -> list of messages/sources

@router.post("/reset_memory/")
async def reset_memory(session_id: str):
    memory_store[session_id] = []
    return {"status": "reset"}

def add_message(session_id: str, role: str, content: str, sources=None):
    if session_id not in memory_store:
        memory_store[session_id] = []
    memory_store[session_id].append({
        "role": role,
        "content": content,
        "sources": sources or []
    })

def get_history(session_id: str):
    return memory_store.get(session_id, [])

def format_sources_for_frontend(session_id: str):
    """
    Returns sources with readable previews for the frontend
    """
    history = get_history(session_id)
    formatted = []
    for entry in history:
        if "sources" in entry:
            for s in entry["sources"]:
                # Only include clean preview text
                formatted.append({
                    "filename": s.get("filename", "unknown"),
                    "preview": s.get("preview", "")  # already cleaned in ingestion
                })
    return formatted