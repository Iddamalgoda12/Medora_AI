from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from app.repositories.hospital_repository import HospitalRepository

_hospital_repository = HospitalRepository()


def _wrap(data: Any, success: bool = True, message: str | None = None, error: str | None = None) -> dict[str, Any]:
    return {"success": success, "message": message, "data": data, "error": error}


@tool("get_all_hospitals")
def get_all_hospitals(limit: int | None = None) -> dict[str, Any]:
    """Return all hospitals, optionally limited to the first N entries."""
    hospitals = _hospital_repository.get_all()
    if limit is not None:
        hospitals = hospitals[:limit]
    return _wrap({"results": hospitals, "total": len(hospitals)}, message="Hospitals retrieved successfully")


@tool("get_hospital_details")
def get_hospital_details(hospital_id: str) -> dict[str, Any]:
    """Return details for a single hospital by ID."""
    hospital = _hospital_repository.get_by_id(hospital_id)
    if not hospital:
        return _wrap(None, success=False, message="Hospital not found", error=f"No hospital matched hospital_id={hospital_id}")
    return _wrap(hospital, message="Hospital details retrieved successfully")


@tool("search_hospitals")
def search_hospitals(query: str | None = None, city: str | None = None, limit: int = 10) -> dict[str, Any]:
    """Search hospitals by text query and/or city."""
    results = _hospital_repository.search(query=query, city=city, limit=limit)
    return _wrap({"results": results, "total": len(results)}, message="Hospital search completed")
