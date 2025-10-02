# app.py
import streamlit as st
import requests
import uuid
import json
import os
from dotenv import load_dotenv

# ---------- CONFIG ----------
load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
# ----------------------------

st.set_page_config(page_title="Enterprise RAG (Streamlit)", layout="wide")

# --- SSE Stream Helper ---
def sse_stream_post(url, json_data=None, timeout=60):
    """
    Minimal SSE client using POST + requests. 
    Yields parsed JSON payloads from lines that start with "data: ".
    """
    with requests.post(url, json=json_data, stream=True, timeout=timeout) as resp:
        resp.raise_for_status()
        buffer = ""
        for raw_line in resp.iter_lines(decode_unicode=True):
            if raw_line is None:
                continue
            line = raw_line.strip()
            if not line:
                if buffer:
                    for l in buffer.splitlines():
                        l = l.strip()
                        if l.startswith("data:"):
                            payload = l[len("data:"):].strip()
                            try:
                                yield json.loads(payload)
                            except Exception:
                                yield {"type": "raw", "value": payload}
                    buffer = ""
                continue
            buffer += line + "\n"
        if buffer:
            for l in buffer.splitlines():
                l = l.strip()
                if l.startswith("data:"):
                    payload = l[len("data:"):].strip()
                    try:
                        yield json.loads(payload)
                    except Exception:
                        yield {"type": "raw", "value": payload}


# --- Session state ---
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "sources" not in st.session_state:
    st.session_state.sources = []
if "last_assistant" not in st.session_state:
    st.session_state.last_assistant = None
if "is_streaming" not in st.session_state:
    st.session_state.is_streaming = False


# --- Layout: left pane upload + controls, right pane chat display ---
col_left, col_right = st.columns([1, 2])

with col_left:
    st.header("Documents")
    upload_file = st.file_uploader("Upload PDF / TXT / DOCX", type=["pdf", "txt", "docx"], accept_multiple_files=False)

    if st.button("Upload & Ingest"):
        if upload_file is None:
            st.warning("Choose a file first.")
        else:
            try:
                files = {"file": (upload_file.name, upload_file.getvalue(), upload_file.type)}
                with st.spinner("Uploading and ingesting..."):
                    r = requests.post(f"{BACKEND_URL}/ingest/", files=files, timeout=120)
                    r.raise_for_status()
                st.success("File uploaded and ingested ✅")
            except Exception as e:
                st.error(f"Upload failed: {e}")

    st.markdown("---")
    st.header("Controls")
if st.button("Reset Conversation (clear memory)"):
    try:
        resp = requests.post(
            f"{BACKEND_URL}/reset_memory/?session_id={st.session_state.session_id}",
            timeout=10
        )
        resp.raise_for_status()
        # Clear session state
        st.session_state.messages = []
        st.session_state.sources = []
        st.session_state.last_assistant = None
        st.session_state.session_id = str(uuid.uuid4())
        st.success("Conversation history cleared.")
        
        # Force rerun by modifying a dummy session_state key
        st.session_state._rerun = st.session_state.get("_rerun", 0) + 1

    except Exception as e:
        st.error(f"Reset failed: {e}")

    st.markdown("### Diagnostics")
    st.write(f"Messages: {len(st.session_state.messages)}")
    st.write(f"Sources cached: {len(st.session_state.sources)}")

with col_right:
    st.title("RAG Chat")

    # Chat display box
    chat_box = st.container()
    with chat_box:
        for i, m in enumerate(st.session_state.messages):
            if m["role"] == "user":
                st.markdown(f"<div style='text-align:right'><b>You:</b> {m['content']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='text-align:left; background:#e0e0e0; color:#111; padding:12px; border-radius:12px;'><b>Assistant:</b> {m['content']}</div>", unsafe_allow_html=True)

        if st.session_state.is_streaming:
            st.info("Assistant is typing...")

        if st.session_state.sources:
            st.markdown("---")
            st.markdown("**Sources**")
            for s in st.session_state.sources:
                preview = s.get("preview", "")[:300]
                filename = s.get("filename", "unknown")
                st.markdown(f"- **{filename}** — {preview}...")

    st.markdown("---")

    # Input
    with st.form("query_form", clear_on_submit=False):
        user_input = st.text_input("Ask a question:", key="user_input")
        submitted = st.form_submit_button("Send")

    if submitted and user_input.strip():
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.sources = []
        st.session_state.last_assistant = None
        st.session_state.is_streaming = True

        assistant_placeholder = st.empty()
        source_placeholder = st.empty()
        final_answer_parts = []

        try:
            url = f"{BACKEND_URL}/query_sse_memory/"
            data = {"query": user_input, "session_id": st.session_state.session_id}

            for event in sse_stream_post(url, json_data=data, timeout=300):
                t = event.get("type")
                if t == "token":
                    token = event.get("value", "")
                    final_answer_parts.append(token)
                    joined = "".join(final_answer_parts)
                    assistant_placeholder.markdown(
                        f"<div style='text-align:left; background:#e0e0e0; color:#111; padding:12px; border-radius:12px;'><b>Assistant:</b> {joined}</div>",
                        unsafe_allow_html=True
                    )
                elif t == "sources":
                    st.session_state.sources = event.get("value", [])
                    src_md = "<b>Sources:</b><br>"
                    for s in st.session_state.sources:
                        preview = s.get("preview", "")[:300]
                        filename = s.get("filename", "unknown")
                        src_md += f"- **{filename}** — {preview}...<br>"
                    source_placeholder.markdown(src_md, unsafe_allow_html=True)
                elif t == "done":
                    final_answer = "".join(final_answer_parts).strip()
                    st.session_state.messages.append({"role": "assistant", "content": final_answer})
                    st.session_state.last_assistant = final_answer
                    st.session_state.is_streaming = False
                    assistant_placeholder.markdown(
                        f"<div style='text-align:left; background:#e0e0e0; color:#111; padding:12px; border-radius:12px;'><b>Assistant:</b> {final_answer}</div>",
                        unsafe_allow_html=True
                    )
                    break
        except Exception as e:
            st.error(f"Error during streaming: {e}")
            st.session_state.is_streaming = False

    # Feedback UI
    if st.session_state.last_assistant:
        st.markdown("### Feedback")
        col1, col2, col3 = st.columns([1, 1, 6])
        with col1:
            if st.button("👍 Helpful"):
                try:
                    payload = {
                        "query": st.session_state.messages[-2]["content"] if len(st.session_state.messages) >= 2 else "",
                        "answer": st.session_state.last_assistant,
                        "is_helpful": True,
                        "sources": st.session_state.sources,
                        "session_id": st.session_state.session_id
                    }
                    r = requests.post(f"{BACKEND_URL}/feedback/", json=payload, timeout=10)
                    r.raise_for_status()
                    st.success("Thanks for the feedback!")
                except Exception as e:
                    st.error(f"Failed to send feedback: {e}")
        with col2:
            if st.button("👎 Not helpful"):
                try:
                    payload = {
                        "query": st.session_state.messages[-2]["content"] if len(st.session_state.messages) >= 2 else "",
                        "answer": st.session_state.last_assistant,
                        "is_helpful": False,
                        "sources": st.session_state.sources,
                        "session_id": st.session_state.session_id
                    }
                    r = requests.post(f"{BACKEND_URL}/feedback/", json=payload, timeout=10)
                    r.raise_for_status()
                    st.success("Thanks — noted.")
                except Exception as e:
                    st.error(f"Failed to send feedback: {e}")

st.markdown("---")
st.markdown("Tip: Upload documents first, then ask questions referencing the uploaded content.")