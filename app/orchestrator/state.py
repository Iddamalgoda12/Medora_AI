from __future__ import annotations

from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from langgraph.managed import RemainingSteps


SupportedDomain = Literal[
    "doctor",
    "booking",
    "hospital",
    "pharmacy",
    "emergency",
    "rag",
    "memory",
    "profile",
    "unknown",
]


class DomainContext(TypedDict, total=False):
    intent: str
    selected_id: str
    selected_ids: list[str]
    last_result_ids: list[str]
    last_tool: str
    filters_applied: dict[str, Any]
    search_query: dict[str, Any]


class AgentState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    remaining_steps: RemainingSteps
    
    user_profile: dict[str, Any]
    memory: Any
    tool_results: list[dict[str, Any]]
    conversation_context: str
    error: str
    active_domain: SupportedDomain
    response: str
    final_response: str
    execution_trace: list[str]
    routing_reason: str
    domain_context: DomainContext
    domain_contexts: dict[str, DomainContext]
    search_query: dict[str, Any]
    chat_history: list[dict[str, Any]]
    metadata: dict[str, Any]
