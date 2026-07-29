from app.orchestrator.state import AgentState
from app.memory.mem0_service import memory_service


def _get_final_response(state: AgentState) -> str:
    return state.get("final_response") or state.get("response") or ""


async def memory_save_node(state: AgentState, user_id: str) -> AgentState:
    try:
        final_response = _get_final_response(state)
        user_messages = [
            message
            for message in (state.get("messages") or [])
            if getattr(message, "type", "") == "human"
        ]
        user_message = getattr(user_messages[-1], "content", "") if user_messages else ""

        if not user_message or not final_response.strip():
            return state

        messages = [
            {
                "role": "user",
                "content": user_message,
            },
            {
                "role": "assistant",
                "content": final_response,
            },
        ]

        memory_service.memory.add(messages=messages, user_id=user_id)

        return {
            **state,
            "execution_trace": [
                *state.get("execution_trace", []),
                "Memory stored",
            ]
        }

    except Exception as e:
        return {
            **state,
            "execution_trace": [
                *state.get("execution_trace", []),
                f"Memory Error: {e}",
            ]
        }
