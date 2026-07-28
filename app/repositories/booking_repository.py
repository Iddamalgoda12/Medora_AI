from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


class BookingRepository:
    def __init__(self) -> None:
        self._path = Path(__file__).resolve().parent.parent / "database" / "bookings.json"
        self._cache: list[dict[str, Any]] | None = None

    def _load(self) -> list[dict[str, Any]]:
        if self._cache is None:
            if not self._path.exists() or self._path.stat().st_size == 0:
                self._cache = []
            else:
                self._cache = json.loads(self._path.read_text(encoding="utf-8"))
        return self._cache

    def get_booking(self, booking_id: str) -> dict[str, Any] | None:
        for booking in self._load():
            if booking.get("booking_id") == booking_id:
                return deepcopy(booking)
        return None

    def get_all_bookings(self) -> list[dict[str, Any]]:
        return deepcopy(self._load())

    def create_booking(self, booking: dict[str, Any]) -> dict[str, Any]:
        items = self._load()
        booking = dict(booking)
        booking.setdefault("booking_id", f"B{len(items)+1:03d}")
        items.append(booking)
        self._path.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
        return deepcopy(booking)

    def update_booking(self, booking_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        items = self._load()
        for index, booking in enumerate(items):
            if booking.get("booking_id") == booking_id:
                items[index] = {**booking, **updates}
                self._path.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
                return deepcopy(items[index])
        return None

    def cancel_booking(self, booking_id: str) -> dict[str, Any] | None:
        return self.update_booking(booking_id, {"booking_status": "cancelled"})

    def search(self, query: str | None = None, doctor_id: str | None = None, patient_name: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
        query_l = (query or "").lower()
        patient_l = (patient_name or "").lower()
        results = []
        for booking in self._load():
            blob = " ".join(str(booking.get(field, "")) for field in ("booking_id", "doctor_id", "patient_name", "reason")).lower()
            if query_l and query_l not in blob:
                continue
            if doctor_id and booking.get("doctor_id") != doctor_id:
                continue
            if patient_l and patient_l not in str(booking.get("patient_name", "")).lower():
                continue
            results.append(deepcopy(booking))
            if len(results) >= limit:
                break
        return results
