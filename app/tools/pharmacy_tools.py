from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from app.repositories.pharmacy_repository import PharmacyRepository

_pharmacy_repository = PharmacyRepository()


def _wrap(data: Any, success: bool = True, message: str | None = None, error: str | None = None) -> dict[str, Any]:
    return {"success": success, "message": message, "data": data, "error": error}


@tool("get_all_pharmacies")
def get_all_pharmacies(limit: int | None = None) -> dict[str, Any]:
    """Return all pharmacies, optionally limited to the first N entries."""
    pharmacies = _pharmacy_repository.get_all()
    if limit is not None:
        pharmacies = pharmacies[:limit]
    return _wrap({"results": pharmacies, "total": len(pharmacies)}, message="Pharmacies retrieved successfully")


@tool("get_pharmacy_details")
def get_pharmacy_details(pharmacy_id: str) -> dict[str, Any]:
    """Return details for a single pharmacy by ID."""
    pharmacy = _pharmacy_repository.get_by_id(pharmacy_id)
    if not pharmacy:
        return _wrap(None, success=False, message="Pharmacy not found", error=f"No pharmacy matched pharmacy_id={pharmacy_id}")
    return _wrap(pharmacy, message="Pharmacy details retrieved successfully")


@tool("search_pharmacies")
def search_pharmacies(query: str | None = None, city: str | None = None, limit: int = 10) -> dict[str, Any]:
    """Search pharmacies by text query and/or city."""
    results = _pharmacy_repository.search(query=query, city=city, limit=limit)
    return _wrap({"results": results, "total": len(results)}, message="Pharmacy search completed")
