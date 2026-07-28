from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

from app.repositories.booking_repository import BookingRepository

_booking_repository = BookingRepository()


def _wrap(data: Any, success: bool = True, message: str | None = None, error: str | None = None) -> dict[str, Any]:
    return {"success": success, "message": message, "data": data, "error": error}


@tool("get_booking")
def get_booking(booking_id: str) -> dict[str, Any]:
    """Return a single booking by booking ID."""
    booking = _booking_repository.get_booking(booking_id)
    if not booking:
        return _wrap(None, success=False, message="Booking not found", error=f"No booking matched booking_id={booking_id}")
    return _wrap(booking, message="Booking retrieved successfully")


@tool("get_bookings")
def get_bookings(limit: int | None = None) -> dict[str, Any]:
    """Return all bookings, optionally limited to the first N entries."""
    bookings = _booking_repository.get_all_bookings()
    if limit is not None:
        bookings = bookings[:limit]
    return _wrap({"results": bookings, "total": len(bookings)}, message="Bookings retrieved successfully")


@tool("create_booking")
def create_booking(booking: dict[str, Any]) -> dict[str, Any]:
    """Create a booking record and persist it to the booking database."""
    created = _booking_repository.create_booking(booking)
    return _wrap(created, message="Booking created successfully")


@tool("search_bookings")
def search_bookings(query: str | None = None, doctor_id: str | None = None, patient_name: str | None = None, limit: int = 10) -> dict[str, Any]:
    """Search bookings by text query, doctor ID, and/or patient name."""
    results = _booking_repository.search(query=query, doctor_id=doctor_id, patient_name=patient_name, limit=limit)
    return _wrap({"results": results, "total": len(results)}, message="Booking search completed")
