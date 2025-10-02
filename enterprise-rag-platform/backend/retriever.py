from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
import chromadb

client = chromadb.Client()
collection = client.get_or_create_collection("docs")

def query_docs(question: str):
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    vectordb = Chroma(client=client, collection_name="docs", embedding_function=embeddings)

    retriever = vectordb.as_retriever(search_kwargs={"k": 3})
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    qa = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        return_source_documents=True
    )
    
    result = qa.invoke({"query": question})
    answer = result["result"]

    # Build structured sources
    sources = []
    for doc in result["source_documents"]:
        sources.append({
            "filename": doc.metadata.get("filename", "unknown"),
            "preview": doc.page_content[:200]  # first 200 chars as snippet
        })

    return answer, sources