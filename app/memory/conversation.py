from __future__ import annotations

from typing import Any
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from app.llms.llm import ask_llm_async

MAX_RECENT_MESSAGES = 20
SUMMARY_BATCH_SIZE = 10
SUMMARY_MAX_WORDS = 100


def _message_content(message: BaseMessage) -> str:
    return getattr(message, "content", "") or ""


def _copy_state(state: dict[str, Any]) -> dict[str, Any]:
    return {**state}


def _trim_to_recent_messages(messages: list[BaseMessage]) -> list[BaseMessage]:
    if len(messages) <= MAX_RECENT_MESSAGES:
        return messages
    return messages[-MAX_RECENT_MESSAGES:]


def build_conversation_context(state: dict[str, Any]) -> list[BaseMessage]:        #main handler of memory -longterm ,summary and recent messages are combined.
    messages = list(state.get("messages") or [])
    recent_messages = _trim_to_recent_messages(messages)
    conversation_summary = (state.get("conversation_summary") or "").strip()
    memory_context = (state.get("memory") or "").strip()

    context_messages: list[BaseMessage] = []

    if memory_context:
        context_messages.append(
            SystemMessage(
                content=(
                    "Relevant long-term memory from Mem0. "
                    "Use this as background context when helpful:\n"
                    f"{memory_context}"
                )
            )
        )

    if conversation_summary:
        context_messages.append(
            SystemMessage(
                content=(
                    "Conversation summary for context only. "
                    "Use this as background, not as a user message:\n"
                    f"{conversation_summary}"
                )
            )
        )

    if not context_messages:
        return recent_messages

    return [*context_messages, *recent_messages]


async def summarize_old_messages(
    current_summary: str,
    old_messages: list[BaseMessage],
) -> str:
    """Rewrite the running summary from the existing summary and older messages."""
    old_transcript = "\n".join(
        f"{'User' if isinstance(message, HumanMessage) else 'Assistant'}: {_message_content(message)}"
        for message in old_messages
        if _message_content(message).strip()
    )
    existing_summary = current_summary.strip() or "No prior summary."

    prompt = f"""
You are compressing a medical conversation summary for long-term context.

Rules:
- Rewrite the summary from scratch instead of appending.
- Keep it at 300 words maximum.
- Preserve only important ongoing context, preferences, constraints, decisions, symptoms, test results, medications, follow-ups, and open questions.
- Remove obsolete, duplicated, or completed information.
- Do not mention that this is a summary.
- Be concise and clinically useful.

Existing summary:
{existing_summary}

Older messages to incorporate:
{old_transcript}

Return only the rewritten summary.
""".strip()

    summary = (await ask_llm_async(prompt)).strip()
    return _enforce_word_limit(summary)


def _enforce_word_limit(text: str) -> str:
    words = text.split()
    if len(words) <= SUMMARY_MAX_WORDS:
        return text.strip()
    return " ".join(words[:SUMMARY_MAX_WORDS]).strip()


async def manage_conversation_history(state: dict[str, Any]) -> dict[str, Any]:
    """
    Keep only the most recent 20 messages and maintain a compact rolling summary.

    When the message limit is exceeded, the oldest 10 messages are summarized and
    removed so the state stays small and the summary remains the durable memory.
    """
    updated_state = _copy_state(state)
    messages = list(updated_state.get("messages") or [])
    summary = (updated_state.get("conversation_summary") or "").strip()

    while len(messages) >= MAX_RECENT_MESSAGES:
        messages_to_summarize = messages[:SUMMARY_BATCH_SIZE]
        messages = messages[SUMMARY_BATCH_SIZE:]
        summary = await summarize_old_messages(summary, messages_to_summarize)

    updated_state["messages"] = messages
    updated_state["conversation_summary"] = summary
    return updated_state


def strip_conversation_summary_messages(state: dict[str, Any]) -> dict[str, Any]:
    """Remove injected summary messages so they are not persisted in state."""
    updated_state = _copy_state(state)
    messages = list(updated_state.get("messages") or [])
    updated_state["messages"] = [
        message
        for message in messages
        if not (
            isinstance(message, SystemMessage)
            and _message_content(message).startswith(
                "Conversation summary for context only."
            )
        )
    ]
    return updated_state


def last_exchange_context(chat_history: list[dict[str, Any]]) -> str:
    """Format the previous exchange for inclusion in an LLM prompt."""
    if not chat_history:
        return "No previous conversation is available."

    exchange = chat_history[-1]
    return (
        f"Previous user query: {exchange.get('query', '')}\n"
        f"Previous assistant answer: {exchange.get('answer', '')}"
    )


async def remember_exchange_node(state: dict[str, Any]) -> dict[str, Any]:
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
