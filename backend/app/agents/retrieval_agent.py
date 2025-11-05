import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain_community.vectorstores import Chroma
from langchain.memory import ConversationBufferMemory

CHROMA_PATH = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

def get_retriever(k=4):
    """Get a retriever from ChromaDB. Returns None if collection doesn't exist."""
    try:
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        vectordb = Chroma(
            persist_directory=CHROMA_PATH,
            collection_name="pdf_docs",
            embedding_function=embeddings
        )
        # Check if collection has documents
        retriever = vectordb.as_retriever(search_kwargs={"k": k})
        return retriever
    except Exception as e:
        print(f"Error getting retriever: {e}")
        # If collection doesn't exist, create it and return empty retriever
        import chromadb
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        try:
            client.create_collection("pdf_docs")
            vectordb = Chroma(
                persist_directory=CHROMA_PATH,
                collection_name="pdf_docs",
                embedding_function=embeddings
            )
            return vectordb.as_retriever(search_kwargs={"k": k})
        except:
            raise ValueError(f"Could not initialize ChromaDB collection: {e}")

def make_conversational_agent():
    """Create a conversational retrieval agent with RAG capabilities."""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    chat = ChatOpenAI(
        temperature=0.0,
        openai_api_key=OPENAI_API_KEY,
        model="gpt-3.5-turbo"  # Use cost-effective model
    )
    retriever = get_retriever()
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer"
    )
    qa = ConversationalRetrievalChain.from_llm(
        chat,
        retriever=retriever,
        memory=memory,
        return_source_documents=False,
        verbose=False
    )
    return qa

