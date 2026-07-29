import logging
from langchain_core.messages import AIMessage, HumanMessage

from app.orchestrator.agent import invoke_medora_agent
from app.nodes.memory_node import memory_node
from app.nodes.memory_save_node import memory_save_node
from app.memory.conversation import (
    build_conversation_context,
    manage_conversation_history,
    strip_conversation_summary_messages,
)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


def create_initial_state():
    return {
        "messages": [],
        "user_profile": {},
        "memory": None,
        "conversation_summary": "",
        "tool_results": [],
        "conversation_context": "",
        "error": "",
        "active_domain": "unknown",
        "response": "",
        "final_response": "",
        "execution_trace": [],
        "routing_reason": "",
        "domain_context": {},
        "domain_contexts": {},
        "search_query": {},
        "chat_history": [],
        "metadata": {},
    }


async def run_agent(state, user_input, thread_id: str):
    state["messages"].append(HumanMessage(content=user_input))
    state = await memory_node(state, user_id=thread_id)
    state["messages"] = build_conversation_context(state)     #long term memry and summary all gets added here to messages.
    state["response"] = ""
    state["final_response"] = ""
    state["error"] = ""
    state["execution_trace"] = []
    state["domain_context"] = state.get("domain_context") or {}
    state["domain_context"]["last_user_message"] = user_input

    result = invoke_medora_agent(
        state,
        thread_id=thread_id,
    )
    result = strip_conversation_summary_messages(result)     # result means the updated state
    result = await manage_conversation_history(result)
    messages = result.get("messages") or []
    if messages and isinstance(messages[-1], AIMessage):
        result["response"] = messages[-1].content
    elif messages:
        result["response"] = getattr(messages[-1], "content", "") or ""
    result["final_response"] = result.get("response", "")
    result = await memory_save_node(result, user_id=thread_id)
    log_agent_run(result)

    return result


def log_agent_run(state):
    """Print a compact routing summary to the backend terminal."""
    execution_trace = state.get("execution_trace", [])
    response = state.get("response", "")

    if execution_trace:
        logger.info("Execution trace: %s", " -> ".join(execution_trace))

    if response:
        preview = response.strip().replace("\n", " ")
        logger.info("Response preview: %s", preview[:200])
