from typing import Any, Dict, List


def last_exchange_context(chat_history: List[Dict[str, Any]]) -> str:
    """Format the previous exchange for inclusion in an LLM prompt."""
    if not chat_history:
        return "No previous conversation is available."

    exchange = chat_history[-1]
    return (
        f"Previous user query: {exchange.get('query', '')}\n"
        f"Previous assistant answer: {exchange.get('answer', '')}"
    )


async def remember_exchange_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Keep only the most recent completed user/assistant exchange."""
    answer = state.get("response") or state.get("final_response", "")
    if not answer:
        return state

    return {
        **state,
        "chat_history": [{"query": state.get("query", ""), "answer": answer}],
        "execution_trace": [
            *state.get("execution_trace", []),
            "remember_exchange",
        ],
    }
