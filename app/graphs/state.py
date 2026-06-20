from typing import TypedDict, List


class AgentState(TypedDict):
    query: str
    response: str
    routes: list[str]
    retrieved_docs: List[str]
    execution_trace: List[str]
    chat_history: List[dict]
   
    rag_result: str
    memory_result: str
    web_result: str
    tool_result: str
    chat_result: str

    final_answer: str
