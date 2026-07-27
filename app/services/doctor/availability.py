from __future__ import annotations

from datetime import date
from typing import Any

from app.services.doctor.schemas import AvailableSlot


def _remaining_capacity(schedule: dict[str, Any]) -> int:
    max_patients = int(schedule.get("max_patients") or 0)
    booked_patients = int(schedule.get("booked_patients") or 0)
    return max(max_patients - booked_patients, 0)


def has_available_slot(schedule: dict[str, Any]) -> bool:
    return schedule.get("status") == "available" and _remaining_capacity(schedule) > 0


def find_next_available_slot(schedules: list[dict[str, Any]]) -> dict[str, Any] | None:
    future_slots = [slot for slot in schedules if has_available_slot(slot)]
    future_slots.sort(key=lambda slot: (slot.get("date", ""), slot.get("start_time", "")))
    return future_slots[0] if future_slots else None


def get_available_slots(schedules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    slots: list[dict[str, Any]] = []
    for schedule in schedules:
        schedule_date = str(schedule.get("date") or "")
        if schedule_date and schedule_date < date.today().isoformat():
            continue
        if not has_available_slot(schedule):
            continue

        start_time = schedule.get("start_time", "")
        duration = int(schedule.get("duration_minutes") or 0)
        try:
            hour, minute = [int(part) for part in start_time.split(":")[:2]]
            total_minutes = hour * 60 + minute + duration
            end_time = f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"
        except Exception:
            end_time = start_time

        if not end_time:
            hour, minute = (start_time.split(":") + ["00"])[:2]
            total_minutes = int(hour) * 60 + int(minute) + duration
            end_time = f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"

        slots.append(
            AvailableSlot(
                schedule_id=schedule.get("schedule_id"),
                date=schedule.get("date", ""),
                day=schedule.get("day", ""),
                start_time=start_time,
                end_time=end_time,
                available=True,
                location_id=schedule.get("location_id"),
                location_type=schedule.get("location_type"),
                remaining_capacity=_remaining_capacity(schedule),
            ).model_dump()
        )
    return slots


def filter_available(doctors: list[dict[str, Any]], search_request: dict[str, Any], schedules_by_doctor: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    if not search_request.get("available_only", True):
        return doctors

    filtered: list[dict[str, Any]] = []
    for doctor in doctors:
        doctor_id = doctor.get("doctor_id")
        schedule = schedules_by_doctor.get(doctor_id, [])
        if any(has_available_slot(slot) for slot in schedule):
            filtered.append(doctor)
    return filtered
