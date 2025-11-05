import os, uuid
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
import chromadb

CHROMA_PATH = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

def init_chroma():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    try:
        col = client.get_collection("pdf_docs")
    except Exception:
        col = client.create_collection("pdf_docs")
    return client, col

def ingest_pdf_file(pdf_path: str, metadata: dict = None):
    metadata = metadata or {}
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(pages)
    texts = [c.page_content for c in chunks]
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    embs = embeddings.embed_documents(texts)
    client, col = init_chroma()
    ids = [str(uuid.uuid4()) for _ in texts]
    metadatas = []
    for c in chunks:
        mm = metadata.copy()
        try:
            if "page" in c.metadata: mm["page"]=c.metadata["page"]
        except: pass
        metadatas.append(mm)
    col.add(documents=texts, embeddings=embs, ids=ids, metadatas=metadatas)
    print(f"Ingested {len(texts)} chunks from {pdf_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("usage: python ingest_pdf.py path/to/file.pdf")
    else:
        ingest_pdf_file(sys.argv[1])

