from ..rag.retrieval.generator import generate_context
from ..graphs.state import State


async def rag_node(state: State) -> State:
    rag_result = generate_context(state["query"])

    return {
        **state,
        "rag_result": rag_result,
        "execution_trace": [
            *state["execution_trace"],
            "rag_node"
        ]
    }