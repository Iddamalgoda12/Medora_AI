from typing import TypedDict, List, Optional, Any
from typing import TypedDict, List, Dict, Any, Optional


class State(TypedDict):
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

    # -------------------
    # MedoraAI Fields
    # -------------------

    symptoms: List[str]

    current_goal: str

    urgency: str

    report_uploaded: bool

    medicine_request: bool

    appointment_request: bool

    emergency_flag: bool

    doctor_recommendation: str

    pharmacy_recommendation: str

    appointment_recommendation: str

    patient_analysis: str

    iteration_count: int

    final_answer: str

    # Appointment/Doctor Search specific state fields
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

    execution_trace: List[str]

    final_response: str

    clarification_done: bool

    user_context: Dict[str, Any]

    metadata: Dict[str, Any]

    rag_result: str
