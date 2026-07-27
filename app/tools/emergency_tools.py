from __future__ import annotations

from typing import Any

from langchain_core.tools import tool


def _wrap(data: Any, success: bool = True, message: str | None = None, error: str | None = None) -> dict[str, Any]:
    return {"success": success, "message": message, "data": data, "error": error}


@tool("triage_symptoms")
def triage_symptoms(symptoms: list[str]) -> dict[str, Any]:
    """Triage symptoms and flag whether they appear high risk."""
    symptoms_l = " ".join(symptoms).lower()
    high_risk = any(term in symptoms_l for term in ["chest pain", "shortness of breath", "stroke", "unconscious", "bleeding"])
    return _wrap(
        {"high_risk": high_risk, "symptoms": symptoms, "recommendation": "Seek urgent care" if high_risk else "Monitor and consult a clinician"},
        message="Symptoms triaged successfully",
    )


@tool("assess_emergency")
def assess_emergency(query: str) -> dict[str, Any]:
    """Assess whether the user's message describes an urgent emergency."""
    query_l = query.lower()
    urgent = any(term in query_l for term in ["chest pain", "cannot breathe", "shortness of breath", "stroke", "seizure", "unconscious"])
    return _wrap(
        {"urgent": urgent, "recommendation": "Call emergency services now" if urgent else "Use the doctor flow"},
        message="Emergency assessment completed",
    )


@tool("get_emergency_protocol")
def get_emergency_protocol(category: str) -> dict[str, Any]:
    """Return a lightweight emergency protocol for the requested category."""
    protocols = {
        "chest pain": ["Call emergency services", "Stop activity", "Keep patient calm"],
        "shortness of breath": ["Call emergency services", "Sit upright", "Monitor breathing"],
    }
    return _wrap(protocols.get(category.lower(), ["Call emergency services if symptoms worsen"]), message="Emergency protocol retrieved successfully")
