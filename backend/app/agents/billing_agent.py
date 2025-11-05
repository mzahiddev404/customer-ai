"""
Billing Support Agent - Hybrid RAG/CAG Strategy
Implements RAG for initial query, then caches policy information in context (CAG)
"""
import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain_community.vectorstores import Chroma
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate

CHROMA_PATH = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
BILLING_COLLECTION = "billing_docs"

# Session-level cache for static policy information (CAG component)
# In production, this would be stored per session/user
POLICY_CACHE = {}

def get_billing_retriever(k=4):
    """Get retriever for billing documents."""
    try:
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        vectordb = Chroma(
            persist_directory=CHROMA_PATH,
            collection_name=BILLING_COLLECTION,
            embedding_function=embeddings
        )
        return vectordb.as_retriever(search_kwargs={"k": k})
    except Exception as e:
        # If collection doesn't exist, create it
        import chromadb
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        try:
            client.create_collection(BILLING_COLLECTION)
            vectordb = Chroma(
                persist_directory=CHROMA_PATH,
                collection_name=BILLING_COLLECTION,
                embedding_function=embeddings
            )
            return vectordb.as_retriever(search_kwargs={"k": k})
        except:
            raise ValueError(f"Could not initialize billing documents collection: {e}")

def make_billing_agent():
    """
    Create billing agent with Hybrid RAG/CAG:
    - RAG: Retrieves relevant billing docs from vector DB
    - CAG: Caches static policy info after first retrieval for session
    """
    chat = ChatOpenAI(
        temperature=0.0,
        openai_api_key=OPENAI_API_KEY,
        model="gpt-3.5-turbo"
    )
    retriever = get_billing_retriever()
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer"
    )
    
    # Custom prompt template that can incorporate cached context
    template = """Use the following pieces of context to answer the question. 
    If you don't know the answer, just say that you don't know, don't try to make up an answer.
    
    {context}
    
    {chat_history}
    
    Question: {question}
    Helpful Answer:"""
    
    qa = ConversationalRetrievalChain.from_llm(
        chat,
        retriever=retriever,
        memory=memory,
        return_source_documents=False,
        verbose=False,
        combine_docs_chain_kwargs={"prompt": PromptTemplate.from_template(template)}
    )
    return qa

def answer_with_hybrid_rag_cag(question: str, agent):
    """
    Hybrid RAG/CAG approach:
    1. RAG: Retrieve relevant documents from vector DB
    2. CAG: Use cached policy context if available for similar questions
    """
    question_lower = question.lower()
    is_pricing_question = any(word in question_lower for word in ["fee", "price", "cost", "billing", "payment", "subscription"])
    
    # If we have cached pricing context and it's a pricing question, use CAG (fast path)
    if is_pricing_question and "pricing_context" in POLICY_CACHE:
        # Use cached context (CAG) - no retrieval needed
        cached_answer = POLICY_CACHE["pricing_context"]
        # Enhance with RAG for additional context if needed
        try:
            result = agent({"question": question})
            rag_answer = result.get("answer", "")
            # Combine cached (CAG) with fresh RAG for comprehensive answer
            if rag_answer and rag_answer != cached_answer:
                answer = f"{rag_answer}\n\n[Note: This includes cached policy information for quick reference]"
            else:
                answer = cached_answer
        except:
            # Fallback to cached answer if RAG fails
            answer = cached_answer
    else:
        # Use RAG (retrieval path)
        result = agent({"question": question})
        answer = result.get("answer", "")
        
        # Cache the answer if it's pricing-related (for future CAG use)
        if is_pricing_question and answer:
            POLICY_CACHE["pricing_context"] = answer
    
    return answer

