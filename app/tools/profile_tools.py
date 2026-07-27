from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from app.ui.health_profile_manager import load_health_profile, save_health_profile


def _wrap(data: Any, success: bool = True, message: str | None = None, error: str | None = None) -> dict[str, Any]:
    return {"success": success, "message": message, "data": data, "error": error}


@tool("get_health_profile")
def get_health_profile() -> dict[str, Any]:
    """Return the current health profile from storage."""
    return _wrap(load_health_profile(), message="Health profile retrieved successfully")


@tool("update_health_profile")
def update_health_profile(profile: dict[str, Any]) -> dict[str, Any]:
    """Persist the provided health profile to storage."""
    save_health_profile(profile)
    return _wrap(profile, message="Health profile updated successfully")
