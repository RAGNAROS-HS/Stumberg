import os
import glob
from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

load_dotenv(dotenv_path='../.env')
PDF_DIR = "/host_desktop/VU_EXAMS"
INDEX_NAME = "stumberg1"
NAMESPACE = "vu_exams"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
key = os.getenv("PINECONE_API_KEY", "")
pc = Pinecone(api_key=key)
index = pc.Index(INDEX_NAME)
embeddings = OpenAIEmbeddings(model="text-embedding-3-large", dimensions=1024)


loader = DirectoryLoader(PDF_DIR, glob="**/*.pdf", loader_cls=PyPDFLoader)
docs = loader.load()

print(f"Loaded {len(docs)} documents")

splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
chunks = splitter.split_documents(docs)
print(f"Split into {len(chunks)} chunks")

vector_store = PineconeVectorStore.from_documents(chunks, index_name=INDEX_NAME, embedding=embeddings, namespace=NAMESPACE)
print("Vector store created")
