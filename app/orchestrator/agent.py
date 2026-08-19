from __future__ import annotations

from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from app.llms.llm import llm
from app.orchestrator.prompts import  SYSTEM_PROMPT
from app.orchestrator.state import AgentState
from app.tools.booking_tools import create_booking, get_booking, get_bookings, search_bookings
from app.tools.doctor_tools import find_doctors, get_all_doctors, get_available_slots, get_doctor_details
from app.tools.emergency_tools import assess_emergency, get_emergency_protocol, triage_symptoms
from app.tools.hospital_tools import get_all_hospitals, get_hospital_details, search_hospitals
from app.tools.memory_tools import get_conversation_memory, save_conversation_memory
from app.tools.pharmacy_tools import get_all_pharmacies, get_pharmacy_details, search_pharmacies
from app.tools.profile_tools import get_health_profile, update_health_profile
from app.tools.rag_tools import answer_from_documents, search_documents, summarize_documents

memory_checkpointer = MemorySaver()

all_domain_tools = [
    # Doctor
    find_doctors,
    get_doctor_details,
    get_available_slots,
    get_all_doctors,
    # Hospital
    get_all_hospitals,
    get_hospital_details,
    search_hospitals,
    # Booking
    get_booking,
    get_bookings,
    create_booking,
    search_bookings,
    # Pharmacy
    get_all_pharmacies,
    get_pharmacy_details,
    search_pharmacies,
    # Profile / memory
    get_health_profile,
    update_health_profile,
    get_conversation_memory,
    save_conversation_memory,
    # RAG
    search_documents,
    answer_from_documents,
    summarize_documents,
    # Emergency
    triage_symptoms,
    assess_emergency,
    get_emergency_protocol,
]


def build_medora_agent() -> Any:
    """Build the single central Medora AI ReAct agent."""
    return create_react_agent(
        model=llm,
        tools=all_domain_tools,
        prompt="\n\n".join(
            [
                SYSTEM_PROMPT
            ]
        ),
        state_schema=AgentState,
        checkpointer=memory_checkpointer,
    )


medora_agent = build_medora_agent()


def invoke_medora_agent(
    input_state: dict[str, Any],
    *,
    thread_id: str = "medora-default",
    recursion_limit: int = 10,
) -> dict[str, Any]:
    """Invoke the single shared Medora agent."""
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": recursion_limit,
    }
    return medora_agent.invoke(input_state, config=config)
