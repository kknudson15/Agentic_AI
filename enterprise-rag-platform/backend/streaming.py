import json
from fastapi.responses import StreamingResponse
from langchain_openai import ChatOpenAI
from langchain.callbacks.base import BaseCallbackHandler
from backend.mem import add_message, get_history
from backend.hybrid_retriever import query_hybrid

class StreamHandler(BaseCallbackHandler):
    def __init__(self):
        self.queue = []

    def on_llm_new_token(self, token: str, **kwargs):
        self.queue.append(token)

def stream_sse_with_memory(session_id: str, question: str, k: int = 3):
    """
    Stream JSON events over SSE with retrieval + memory.
    Events include tokens, sources, and final done signal.
    """
    # Get hybrid retrieval
    _, sources = query_hybrid(question, k=k)

    # Conversation history
    history = get_history(session_id)
    history_text = "\n".join([f"{m['role']}: {m['content']}" for m in history])

    # Prompt
    prompt = f"""
You are a helpful assistant. Use history and retrieved context.

History:
{history_text}

Retrieved context:
{[s['preview'] for s in sources]}

User: {question}
Assistant:
"""

    # Streaming setup
    handler = StreamHandler()
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=True, callbacks=[handler])
    llm.invoke(prompt)

    def event_generator():
        # Stream tokens
        for token in handler.queue:
            yield f"data: {json.dumps({'type': 'token', 'value': token})}\n\n"
        
        # Final combined answer
        final_answer = "".join(handler.queue).strip()
        add_message(session_id, "user", question)
        add_message(session_id, "assistant", final_answer)

        # Send sources
        yield f"data: {json.dumps({'type': 'sources', 'value': sources})}\n\n"

        # Done signal
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")