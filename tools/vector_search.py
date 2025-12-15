import os
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings  # Or your embedding model
from pinecone import Pinecone
from langchain.tools import tool
from dotenv import load_dotenv

load_dotenv()


key = os.getenv("PINECONE_API_KEY", "")
# Initialize Pinecone client (set PINECONE_API_KEY env var)
pc = Pinecone(api_key=key)
index = pc.Index("stumberg1")  # Your existing index

# Create embeddings (must match what indexed your data)
embeddings = OpenAIEmbeddings(model="text-embedding-3-large", dimensions=1024)

# Define vector store (module/global scope)
vector_store = PineconeVectorStore(index=index, embedding=embeddings, namespace="vu_exams")


@tool(response_format="content_and_artifact")
def retrieve_context(query: str):
    """Retrieve information to help answer a query."""
    retrieved_docs = vector_store.similarity_search(query, k=2)
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\nContent: {doc.page_content}")
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs