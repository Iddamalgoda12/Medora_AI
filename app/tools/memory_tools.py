from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

_conversation_memory: dict[str, Any] = {}


def _wrap(data: Any, success: bool = True, message: str | None = None, error: str | None = None) -> dict[str, Any]:
    return {"success": success, "message": message, "data": data, "error": error}


@tool("get_conversation_memory")
def get_conversation_memory(key: str | None = None) -> dict[str, Any]:
    """Return the stored conversation memory, optionally for one key."""
    if key is None:
        return _wrap(_conversation_memory, message="Conversation memory retrieved successfully")
    return _wrap(_conversation_memory.get(key), message="Conversation memory retrieved successfully")


@tool("save_conversation_memory")
def save_conversation_memory(key: str, value: Any) -> dict[str, Any]:
    """Store a key-value pair in the in-memory conversation cache."""
    _conversation_memory[key] = value
    return _wrap({key: value}, message="Conversation memory saved successfully")
