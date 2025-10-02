from langchain_openai import ChatOpenAI
from backend.hybrid_retriever import query_hybrid

def query_with_memory(session_id: str, question: str, k: int = 3):
    from backend.mem import add_message, get_history
    # Get hybrid retrieval context
    answer, sources = query_hybrid(question, k=k)

    # Build conversation context
    history = get_history(session_id)
    history_text = "\n".join([f"{m['role']}: {m['content']}" for m in history])

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = f"""
You are a helpful assistant. Use conversation history and retrieval context.

History:
{history_text}

Context (retrieved docs):
{[s['preview'] for s in sources]}

User: {question}
Assistant:"""

    final_answer = llm.invoke(prompt).content

    # Store messages in memory
    add_message(session_id, "user", question)
    add_message(session_id, "assistant", final_answer)

    return final_answer, sources