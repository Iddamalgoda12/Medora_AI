from langgraph.graph import StateGraph, START, END

from app.graphs.state import AgentState
from app.agents.appointment_agent import appointment_agent


def route_after_appointment(state):

    if state["needs_user_input"]:
        return "end"

    return "done"


def build_graph():

    builder = StateGraph(AgentState)

    builder.add_node(
        "appointment_agent",
        appointment_agent
    )

    builder.add_edge(
        START,
        "appointment_agent"
    )

    builder.add_conditional_edges(
        "appointment_agent",
        route_after_appointment,
        {
            "end": END,
            "done": END
        }
    )

    return builder.compile()