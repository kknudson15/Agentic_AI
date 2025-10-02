import io
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from docx import Document
import pdfplumber
from backend.hybrid_retriever import ingest_for_bm25  # <-- import your BM25 ingestion function

# This is your vector store directory
VECTOR_STORE_DIR = "vector_store"

# ---------- Text extraction helpers ----------
def extract_text_from_pdf(file_bytes: bytes) -> str:
    text = ""
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()

def extract_text_from_docx(file_bytes: bytes) -> str:
    text = ""
    doc = Document(io.BytesIO(file_bytes))
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text.strip()

def extract_text_from_txt(file_bytes: bytes) -> str:
    return file_bytes.decode(errors="ignore").strip()

def extract_preview(file_bytes: bytes, filename: str) -> str:
    filename = filename.lower()
    if filename.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)[:300]
    elif filename.endswith(".docx"):
        return extract_text_from_docx(file_bytes)[:300]
    elif filename.endswith(".txt"):
        return extract_text_from_txt(file_bytes)[:300]
    else:
        return "Preview not available"

# ---------- Main ingestion ----------
def ingest_document(file_bytes: bytes, filename: str):
    text = ""
    filename_lower = filename.lower()
    if filename_lower.endswith(".pdf"):
        text = extract_text_from_pdf(file_bytes)
    elif filename_lower.endswith(".docx"):
        text = extract_text_from_docx(file_bytes)
    elif filename_lower.endswith(".txt"):
        text = extract_text_from_txt(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {filename}")

    # --- Add to Chroma vector store ---
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    vectorstore = Chroma(persist_directory=VECTOR_STORE_DIR, embedding_function=embeddings)
    vectorstore.add_texts([text], metadatas=[{"filename": filename, "preview": extract_preview(file_bytes, filename)}])
    vectorstore.persist()

    # --- Add to BM25 index for sparse retrieval ---
    # Split text into smaller chunks (optional, improves BM25 granularity)
    chunk_size = 500
    text_chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    ingest_for_bm25(text_chunks, filename)