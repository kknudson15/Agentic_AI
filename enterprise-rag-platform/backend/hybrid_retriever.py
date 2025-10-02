from rank_bm25 import BM25Okapi
from langchain_openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
import chromadb

client = chromadb.Client()
collection = client.get_or_create_collection("docs")

# Build BM25 index
bm25_corpus = []   # list of tokenized chunks
bm25_lookup = []   # mapping back to docs

def build_bm25_index(docs):
    global bm25_corpus, bm25_lookup
    bm25_corpus = [doc["text"].split() for doc in docs]
    bm25_lookup = docs
    return BM25Okapi(bm25_corpus)

bm25 = None

def ingest_for_bm25(text_chunks, filename):
    global bm25, bm25_lookup
    new_docs = [{"filename": filename, "text": chunk} for chunk in text_chunks]
    if bm25 is None:
        bm25 = build_bm25_index(new_docs)
    else:
        bm25_corpus.extend([doc["text"].split() for doc in new_docs])
        bm25_lookup.extend(new_docs)
        bm25 = BM25Okapi(bm25_corpus)

def query_hybrid(question: str, k: int = 3):
    if bm25 is None:
        raise ValueError("BM25 index not initialized. Call ingest_for_bm25 first.")

    # Dense retriever
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    vectordb = Chroma(client=client, collection_name="docs", embedding_function=embeddings)
    dense_results = vectordb.similarity_search(question, k=k)

    # Sparse retriever
    bm25_scores = bm25.get_scores(question.split())
    top_sparse = sorted(
        zip(bm25_scores, bm25_lookup),
        key=lambda x: x[0],
        reverse=True
    )[:k]

    # Fusion
    combined = []
    for doc in dense_results:
        combined.append({
            "filename": doc.metadata.get("filename", "unknown"),
            "preview": doc.page_content[:200],
            "score": 1.0
        })
    for score, doc in top_sparse:
        combined.append({
            "filename": doc["filename"],
            "preview": doc["text"][:200],
            "score": float(score)
        })

    # Deduplicate
    seen = set()
    deduped = []
    for doc in combined:
        if doc["preview"] not in seen:
            deduped.append(doc)
            seen.add(doc["preview"])

    # Answer with LLM
    retriever_docs = [d["preview"] for d in deduped[:k]]
    context = "\n\n".join(retriever_docs)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = f"Answer the following using the context below:\n\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"
    answer = llm.invoke(prompt).content

    return answer, deduped[:k]