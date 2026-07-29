""" retreive from memory service and add to state """

from collections.abc import Mapping, Sequence

from app.orchestrator.state import AgentState
from app.memory.mem0_service import memory_service


def _format_memories(memories: object) -> str:
    if isinstance(memories, Mapping):
        results = memories.get("results", [])
    elif isinstance(memories, Sequence) and not isinstance(memories, (str, bytes)):
        results = memories
    else:
        results = []

    if not results:
        return ""

    return "\n".join(
        item.get("memory", "")
        for item in results
        if item.get("memory")
    )


async def memory_node(state: AgentState, user_id: str) -> AgentState:
    messages = state.get("messages") or []
    user_message = ""
    for message in reversed(messages):                                #gets the last human message from the messages list and breaks the loop
        if getattr(message, "type", "") == "human":
            user_message = getattr(message, "content", "") or ""
            break

    memories = (
        memory_service.memory.search(
            query=user_message,
            filters={"user_id": user_id},
        )
        if user_message
        else {}
    )
    memory_text = _format_memories(memories)

    return {
        **state,
        "memory": memory_text,
        "memory_result": memory_text,
        "execution_trace": [
            *state.get("execution_trace", []),
            "Memory searched",
        ]
    }
