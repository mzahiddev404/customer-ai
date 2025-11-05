"""
Policy & Compliance Agent - Pure CAG Strategy
Uses only static context from pre-loaded policy documents (no vector retrieval)
"""
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Static policy context (in production, this would be loaded from files)
POLICY_CONTEXT = """
POLICY & COMPLIANCE DOCUMENTS:

Terms of Service:
- Users must comply with all applicable laws and regulations
- Service is provided "as is" without warranties
- Users are responsible for maintaining account security

Privacy Policy:
- We collect data necessary for service provision
- User data is encrypted and stored securely
- We do not sell user data to third parties
- Users can request data deletion at any time

Compliance Requirements:
- All transactions must comply with financial regulations
- User verification is required for certain operations
- We maintain audit logs for compliance purposes
"""

def make_policy_agent():
    """
    Create policy agent with Pure CAG (Context-Augmented Generation).
    Uses static policy context without vector retrieval.
    """
    chat = ChatOpenAI(
        temperature=0.0,
        openai_api_key=OPENAI_API_KEY,
        model="gpt-3.5-turbo"
    )
    
    # Create prompt template with static policy context
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"You are a Policy & Compliance assistant. Answer questions based ONLY on the following policy documents:\n\n{POLICY_CONTEXT}\n\nAlways cite which policy document you're referencing."),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}")
    ])
    
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )
    
    # Chain with static context (CAG)
    chain = prompt | chat
    return chain, memory

def answer_with_cag(question: str, chain, memory):
    """
    Pure CAG: Answer using only static context, no retrieval.
    """
    # Get chat history
    chat_history = memory.chat_memory.messages if hasattr(memory, 'chat_memory') else []
    
    # Invoke chain with question and history
    response = chain.invoke({
        "question": question,
        "chat_history": chat_history
    })
    
    # Save to memory
    memory.save_context({"input": question}, {"output": response.content})
    
    return response.content

