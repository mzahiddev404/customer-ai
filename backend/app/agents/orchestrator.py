"""
Orchestrator Agent - LangGraph-based supervisor
Routes queries to appropriate specialized worker agents
"""
import os
from typing import Literal, TypedDict
from langchain.chat_models import ChatOpenAI
from langchain_aws import ChatBedrock
from langchain.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
USE_BEDROCK = os.getenv("USE_BEDROCK", "false").lower() == "true"

# Agent types
AGENT_TYPES = Literal["billing", "technical", "policy", "general"]

class AgentState(TypedDict):
    """State for the agent workflow."""
    question: str
    agent_type: str
    answer: str
    chat_history: list

def get_orchestrator_llm():
    """Get LLM for orchestrator - use AWS Bedrock for cost-effective routing."""
    if USE_BEDROCK:
        try:
            return ChatBedrock(
                model_id="anthropic.claude-3-haiku-20240307-v1:0",
                region_name=AWS_REGION,
                temperature=0.0
            )
        except Exception as e:
            print(f"Bedrock not available, falling back to OpenAI: {e}")
    
    # Fallback to OpenAI
    return ChatOpenAI(
        temperature=0.0,
        openai_api_key=OPENAI_API_KEY,
        model="gpt-3.5-turbo"  # Cost-effective for routing
    )

def route_question(state: AgentState) -> AgentState:
    """
    Route question to appropriate agent using LLM classification.
    """
    question = state["question"]
    
    # Classification prompt
    classification_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a routing agent. Classify the user's question into one of these categories:
- "billing": Questions about fees, pricing, invoices, payments, subscriptions, account tiers
- "technical": Questions about API, login issues, data feeds, troubleshooting, bugs, technical problems
- "policy": Questions about Terms of Service, Privacy Policy, compliance, legal matters, data privacy
- "general": General questions that don't fit the above categories

Respond with ONLY the category name (billing, technical, policy, or general)."""),
        ("human", "{question}")
    ])
    
    llm = get_orchestrator_llm()
    chain = classification_prompt | llm
    response = chain.invoke({"question": question})
    
    agent_type = response.content.strip().lower()
    
    # Validate agent type
    if agent_type not in ["billing", "technical", "policy", "general"]:
        agent_type = "general"
    
    return {**state, "agent_type": agent_type}

def call_billing_agent(state: AgentState) -> AgentState:
    """Call billing support agent."""
    from agents.billing_agent import make_billing_agent, answer_with_hybrid_rag_cag
    
    try:
        agent = make_billing_agent()
        answer = answer_with_hybrid_rag_cag(state["question"], agent)
        if not answer:
            answer = "I couldn't find information about billing. Please ensure billing documents are uploaded."
    except Exception as e:
        answer = f"I encountered an error while processing your billing question: {str(e)}"
    
    return {**state, "answer": answer}

def call_technical_agent(state: AgentState) -> AgentState:
    """Call technical support agent."""
    from agents.technical_agent import make_technical_agent
    
    try:
        agent = make_technical_agent()
        result = agent({"question": state["question"]})
        answer = result.get("answer", "I couldn't find relevant technical information. Please ensure technical documents are uploaded.")
    except Exception as e:
        answer = f"I encountered an error while processing your technical question: {str(e)}"
    
    return {**state, "answer": answer}

def call_policy_agent(state: AgentState) -> AgentState:
    """Call policy & compliance agent."""
    from agents.policy_agent import make_policy_agent, answer_with_cag
    
    try:
        chain, memory = make_policy_agent()
        answer = answer_with_cag(state["question"], chain, memory)
        if not answer:
            answer = "I couldn't generate a policy response. Please try rephrasing your question."
    except Exception as e:
        answer = f"I encountered an error while processing your policy question: {str(e)}"
    
    return {**state, "answer": answer}

def call_general_agent(state: AgentState) -> AgentState:
    """Call general agent (fallback)."""
    from agents.retrieval_agent import make_conversational_agent
    
    try:
        agent = make_conversational_agent()
        result = agent({"question": state["question"]})
        answer = result.get("answer", "I couldn't generate a response.")
    except Exception as e:
        answer = f"I'm sorry, I encountered an error: {str(e)}"
    
    return {**state, "answer": answer}

def should_route(state: AgentState) -> str:
    """Decide which agent to route to."""
    agent_type = state.get("agent_type", "general")
    return agent_type

def create_orchestrator_graph():
    """Create the LangGraph workflow."""
    # Create workflow
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("route", route_question)
    workflow.add_node("billing", call_billing_agent)
    workflow.add_node("technical", call_technical_agent)
    workflow.add_node("policy", call_policy_agent)
    workflow.add_node("general", call_general_agent)
    
    # Set entry point
    workflow.set_entry_point("route")
    
    # Add conditional routing
    workflow.add_conditional_edges(
        "route",
        should_route,
        {
            "billing": "billing",
            "technical": "technical",
            "policy": "policy",
            "general": "general"
        }
    )
    
    # All agents end
    workflow.add_edge("billing", END)
    workflow.add_edge("technical", END)
    workflow.add_edge("policy", END)
    workflow.add_edge("general", END)
    
    # Compile with memory
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    
    return app

# Cache the graph instance
_orchestrator_graph = None

def get_orchestrator_graph():
    """Get or create orchestrator graph (cached)."""
    global _orchestrator_graph
    if _orchestrator_graph is None:
        _orchestrator_graph = create_orchestrator_graph()
    return _orchestrator_graph

def orchestrate_question(question: str, config: dict = None, thread_id: str = "default"):
    """
    Main orchestration function.
    
    Args:
        question: User's question
        config: Optional LangGraph configuration
        thread_id: Thread ID for conversation history tracking
    """
    if config is None:
        config = {"configurable": {"thread_id": thread_id}}
    
    app = get_orchestrator_graph()
    
    # Get existing state if available (for conversation history)
    try:
        # Try to get previous state for this thread
        state = app.get_state(config)
        chat_history = state.values.get("chat_history", []) if state.values else []
    except:
        chat_history = []
    
    # Invoke with initial state
    initial_state = {
        "question": question,
        "agent_type": "",
        "answer": "",
        "chat_history": chat_history
    }
    
    result = app.invoke(initial_state, config=config)
    
    # Update chat history with new interaction
    updated_history = chat_history + [
        {"role": "user", "content": question},
        {"role": "assistant", "content": result["answer"]}
    ]
    
    # Update state with new history (for future conversations)
    try:
        app.update_state(config, {"chat_history": updated_history})
    except:
        pass  # If state update fails, continue anyway
    
    return result["answer"]

