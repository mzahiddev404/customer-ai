"""
Technical Support Agent - Pure RAG Strategy
Uses only retrieval-augmented generation from dynamic knowledge base
"""
import os
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.memory import ConversationBufferMemory

CHROMA_PATH = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TECH_COLLECTION = "tech_docs"

def get_technical_retriever(k=5):
    """Get retriever for technical documents."""
    try:
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        vectordb = Chroma(
            persist_directory=CHROMA_PATH,
            collection_name=TECH_COLLECTION,
            embedding_function=embeddings
        )
        return vectordb.as_retriever(search_kwargs={"k": k})
    except Exception as e:
        # If collection doesn't exist, create it
        import chromadb
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        try:
            client.create_collection(TECH_COLLECTION)
            vectordb = Chroma(
                persist_directory=CHROMA_PATH,
                collection_name=TECH_COLLECTION,
                embedding_function=embeddings
            )
            return vectordb.as_retriever(search_kwargs={"k": k})
        except:
            raise ValueError(f"Could not initialize technical documents collection: {e}")

def make_technical_agent():
    """
    Create technical support agent with Pure RAG.
    Always retrieves from dynamic knowledge base (no caching).
    """
    chat = ChatOpenAI(
        temperature=0.0,
        openai_api_key=OPENAI_API_KEY,
        model="gpt-3.5-turbo"
    )
    retriever = get_technical_retriever()
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

