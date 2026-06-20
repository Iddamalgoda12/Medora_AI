from typing import TypedDict, List, Dict, Any, Optional


class State(TypedDict):
    query: str

    next_task: Optional[str]

    pending_tasks: List[str]

    completed_tasks: List[str]

    agent_results: List[Dict[str, Any]]

    decision_scores: Dict[str, int]

    execution_trace: List[str]

    final_response: str

    clarification_done: bool

    user_context: Dict[str, Any]

    metadata: Dict[str, Any]

    rag_result: str