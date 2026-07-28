import logging
from langchain_core.messages import AIMessage, HumanMessage

from app.orchestrator.agent import invoke_medora_agent

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
    state["response"] = ""
    state["error"] = ""
    state["execution_trace"] = []
    state["domain_context"] = state.get("domain_context") or {}
    state["domain_context"]["last_user_message"] = user_input

    result = invoke_medora_agent(
        state,
        thread_id=thread_id,
    )
    messages = result.get("messages") or []
    if messages and isinstance(messages[-1], AIMessage):
        result["response"] = messages[-1].content
    elif messages:
        result["response"] = getattr(messages[-1], "content", "") or ""
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
