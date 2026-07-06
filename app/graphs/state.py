from typing import Any, Dict, List, Optional, TypedDict


class State(TypedDict):
    query: str
    response: str

    routes: List[str]

    retrieved_docs: List[Any]

    execution_trace: List[str]

    chat_history: List[dict]

    rag_result: str
    memory_result: str
    web_result: str
    tool_result: str
    chat_result: str

    # MedoraAI fields
    symptoms: List[str]
    current_goal: str
    urgency: str

    report_uploaded: bool
    medicine_request: bool
    medicine_names: List[str]
    user_location: Optional[Dict[str, Any]]
    appointment_request: bool
    emergency_flag: bool

    doctor_recommendation: str
    pharmacy_recommendation: str
    appointment_recommendation: str
    patient_analysis: str

    iteration_count: int
    final_answer: str

    specialty: Optional[str]
    location: Optional[str]
    needs_user_input: bool
    followup_question: Optional[str]
    doctor_results: List[Any]

    next_task: Optional[str]
    pending_tasks: List[str]
    completed_tasks: List[str]

    agent_results: List[Dict[str, Any]]
    decision_scores: Dict[str, int]

    final_response: str
    clarification_done: bool
    user_context: Dict[str, Any]
    metadata: Dict[str, Any]
