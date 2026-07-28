from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from app.services.doctor.doctor_service import DoctorService
from app.services.doctor.schemas import DoctorSearchRequest

_doctor_service = DoctorService()


def _serialize_response(data: Any, success: bool = True, message: str | None = None, error: str | None = None) -> dict[str, Any]:
    return {
        "success": success,
        "message": message,
        "data": data,
        "error": error,
    }


@tool("find_doctors")
def find_doctors(
    query: str | None = None,
    specialty: str | None = None,
    hospital_id: str | None = None,
    city: str | None = None,
    gender: str | None = None,
    language: str | None = None,
    min_fee: int | None = None,
    max_fee: int | None = None,
    min_experience: int | None = None,
    min_rating: float | None = None,
    accepting_new_patients: bool | None = None,
    available_only: bool = True,
    limit: int = 10,
) -> dict[str, Any]:
    """Search doctors using the provided filters and return ranked matches."""
    request = DoctorSearchRequest(
        query=query,
        specialty=specialty,
        hospital_id=hospital_id,
        city=city,
        gender=gender,  # type: ignore[arg-type]
        language=language,
        min_fee=min_fee,
        max_fee=max_fee,
        min_experience=min_experience,
        min_rating=min_rating,
        accepting_new_patients=accepting_new_patients,
        available_only=available_only,
        limit=limit,
    )
    result = _doctor_service.search_doctors(request)
    return _serialize_response(result.model_dump(), message=result.message)


@tool("get_doctor_details")
def get_doctor_details(doctor_id: str) -> dict[str, Any]:
    """Return the full details for a single doctor by ID."""
    result = _doctor_service.get_doctor_details(doctor_id)
    if result is None:
        return _serialize_response(None, success=False, message="Doctor not found", error=f"No doctor matched doctor_id={doctor_id}")
    return _serialize_response(result.model_dump(), message="Doctor details retrieved successfully")


@tool("get_available_slots")
def get_available_slots(doctor_id: str) -> dict[str, Any]:
    """Return the available appointment slots for a doctor by ID."""
    slots = _doctor_service.get_available_slots(doctor_id)
    return _serialize_response({"doctor_id": doctor_id, "available_slots": slots}, message="Available slots retrieved successfully")


@tool("get_all_doctors")
def get_all_doctors(limit: int | None = None) -> dict[str, Any]:
    """Return the list of doctors, optionally limited to a fixed size."""
    doctors = _doctor_service.get_all_doctors()
    if limit is not None:
        doctors = doctors[:limit]
    return _serialize_response({"results": doctors, "total": len(doctors)}, message="Doctors retrieved successfully")
