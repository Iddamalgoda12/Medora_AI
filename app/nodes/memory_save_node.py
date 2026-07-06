from app.graphs.state import State
from app.memory.mem0_service import memory_service


async def memory_save_node(state: State):
    try:
        messages = [
            {
                "role": "user",
                "content": state["query"],
            },
            {
                "role": "assistant",
                "content": state["final_answer"],
            },
        ]

        memory_service.memory.add(messages)

        return {
            "execution_trace": [
                *state.get("execution_trace", []),
                "Memory stored",
            ]
        }

    except Exception as e:
        return {
            "execution_trace": [
                *state.get("execution_trace", []),
                f"Memory Error: {e}",
            ]
        }