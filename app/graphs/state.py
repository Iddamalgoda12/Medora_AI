from typing import TypedDict, List, Optional, Any


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