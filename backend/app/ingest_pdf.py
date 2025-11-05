import os, uuid
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
import chromadb

CHROMA_PATH = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

def init_chroma(collection_name: str = "pdf_docs"):
    """Initialize ChromaDB collection."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    try:
        col = client.get_collection(collection_name)
    except Exception:
        col = client.create_collection(collection_name)
    return client, col

def get_collection_name(filename: str) -> str:
    """Determine collection name based on filename/content."""
    filename_lower = filename.lower()
    if any(word in filename_lower for word in ["fee", "billing", "price", "payment", "account"]):
        return "billing_docs"
    elif any(word in filename_lower for word in ["tech", "api", "login", "technical", "faq", "bug"]):
        return "tech_docs"
    else:
        return "pdf_docs"  # Default collection

def ingest_pdf_file(pdf_path: str, metadata: dict = None, collection_name: str = None):
    """Ingest PDF into ChromaDB collection."""
    metadata = metadata or {}
    filename = os.path.basename(pdf_path)
    
    # Determine collection name if not provided
    if collection_name is None:
        collection_name = get_collection_name(filename)
    
    loader = PyPDFLoader(pdf_path)
    pages = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(pages)
    texts = [c.page_content for c in chunks]
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    embs = embeddings.embed_documents(texts)
    client, col = init_chroma(collection_name)
    ids = [str(uuid.uuid4()) for _ in texts]
    metadatas = []
    for c in chunks:
        mm = metadata.copy()
        try:
            if "page" in c.metadata: mm["page"]=c.metadata["page"]
        except: pass
        metadatas.append(mm)
    col.add(documents=texts, embeddings=embs, ids=ids, metadatas=metadatas)
    print(f"Ingested {len(texts)} chunks from {pdf_path} into collection '{collection_name}'")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("usage: python ingest_pdf.py path/to/file.pdf")
    else:
        ingest_pdf_file(sys.argv[1])

