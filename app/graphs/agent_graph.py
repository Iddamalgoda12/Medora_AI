from langgraph.graph import END, START, StateGraph

from app.graphs.state import State
from app.agents.decision_engine import decision_engine
from app.agents.appointment_agent import appointment_agent
from app.agents.pharmacy_agent import pharmacy_agent
from app.agents.emergency_agent import emergency_agent
from app.agents.direct_answer_agent import direct_answer_agent
from app.agents.clarifier_agent import clarifier_agent
from app.nodes.rag_node import rag_node
from app.memory.conversation import remember_exchange_node


def route_decision(state: State):
    """
    Route from decision engine to the next task.
    Maps decision engine output names to actual agent node names.
    """
    next_task = state.get("next_task")

    agent_mapping = {
        "pharmacy_agent": "pharmacy_agent",
        "emergency_agent": "emergency_agent",
        "RAG_node": "rag_node",
        "direct_answer": "direct_answer_agent",
        "appointment_agent": "appointment_agent",
        "clarifier_agent": "clarifier_agent",
    }

    return agent_mapping.get(next_task, "clarifier_agent")


def route_after_agent(state: State):
    """Continue multi-step plans when pending tasks remain."""
    if state.get("needs_user_input"):
        return "remember_exchange"
    if state.get("pending_tasks"):
        return "decision_engine"
    return "remember_exchange"


def build_graph():
    """
    Build the LangGraph graph with multi-agent routing and RAG pipeline.

    Flow:
    START
      ↓
    decision_engine
      ↓
    route_decision
      ↓
    agent OR rag_node
      ↓
    END (or back to decision_engine when more tasks remain)
    """
    builder = StateGraph(State)

    builder.add_node("decision_engine", decision_engine)
    builder.add_node("appointment_agent", appointment_agent)
    builder.add_node("pharmacy_agent", pharmacy_agent)
    builder.add_node("emergency_agent", emergency_agent)
    builder.add_node("direct_answer_agent", direct_answer_agent)
    builder.add_node("clarifier_agent", clarifier_agent)

    builder.add_node("rag_node", rag_node)
    builder.add_node("remember_exchange", remember_exchange_node)

    builder.add_edge(START, "decision_engine")

    builder.add_conditional_edges(
        "decision_engine",
        route_decision,
        {
            "appointment_agent": "appointment_agent",
            "pharmacy_agent": "pharmacy_agent",
            "emergency_agent": "emergency_agent",
            "rag_node": "rag_node",
            "direct_answer_agent": "direct_answer_agent",
            "clarifier_agent": "clarifier_agent",
        },
    )

    terminal_agents = [
        "appointment_agent",
        "pharmacy_agent",
        "emergency_agent",
        "direct_answer_agent",
        "clarifier_agent",
        "rag_node",
    ]

    for agent in terminal_agents:
        builder.add_conditional_edges(
            agent,
            route_after_agent,
            {
                "decision_engine": "decision_engine",
                "remember_exchange": "remember_exchange",
            },
        )

    builder.add_edge("remember_exchange", END)

    return builder.compile()
