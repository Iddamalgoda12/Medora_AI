from app.graphs.state import State
from app.memory.mem0_service import memory_service


async def memory_node(state: State):

    memories = memory_service.memory.search(
        query=state["query"]
    )

    memory_text = "\n".join(
        item["memory"]
        for item in memories.get("results", [])
    )

    return {
        "memory_result": memory_text,
        "execution_trace": [
            *state.get("execution_trace", []),
            "Memory searched",
        ]
    }