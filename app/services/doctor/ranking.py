from __future__ import annotations

from typing import Any


def _score_doctor(doctor: dict[str, Any], search_request: dict[str, Any], has_availability: bool) -> float:
    score = 0.0

    rating = float(doctor.get("rating") or 0)
    experience_years = int(doctor.get("experience_years") or 0)
    fee = int(doctor.get("consultation_fee_lkr") or 0)

    score += rating * 4
    score += min(experience_years, 40) * 0.4
    score += 10 if doctor.get("accepting_new_patients") else 0
    score += 8 if has_availability else 0

    max_fee = search_request.get("max_fee")
    min_fee = search_request.get("min_fee")
    if max_fee is not None and fee <= int(max_fee):
        score += 3
    if min_fee is not None and fee >= int(min_fee):
        score += 1

    query = str(search_request.get("query") or "").lower()
    specialty = str(search_request.get("specialty") or "").lower()
    combined = " ".join(
        str(value).lower()
        for value in [
            doctor.get("name"),
            doctor.get("specialization"),
            " ".join(doctor.get("languages") or []),
        ]
        if value
    )
    for token in [query, specialty]:
        if token and token in combined:
            score += 6

    return score


def rank_doctors(
    doctors: list[dict[str, Any]],
    search_request: dict[str, Any],
    schedules_by_doctor: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []
    for doctor in doctors:
        doctor_id = doctor.get("doctor_id")
        has_availability = any(slot.get("status") == "available" for slot in schedules_by_doctor.get(doctor_id, []))
        ranked.append({**doctor, "score": _score_doctor(doctor, search_request, has_availability)})

    ranked.sort(
        key=lambda doctor: (
            float(doctor.get("score") or 0),
            float(doctor.get("rating") or 0),
            int(doctor.get("experience_years") or 0),
        ),
        reverse=True,
    )
    return ranked


def find_similar_doctors(target_doctor: dict[str, Any], doctors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not target_doctor:
        return []

    target_specialization = str(target_doctor.get("specialization") or "").lower()
    target_city_ids = set(target_doctor.get("hospital_ids") or [])
    target_languages = set(target_doctor.get("languages") or [])

    scored: list[dict[str, Any]] = []
    for doctor in doctors:
        if doctor.get("doctor_id") == target_doctor.get("doctor_id"):
            continue
        score = 0.0
        if str(doctor.get("specialization") or "").lower() == target_specialization:
            score += 8
        if target_city_ids.intersection(set(doctor.get("hospital_ids") or [])):
            score += 4
        if target_languages.intersection(set(doctor.get("languages") or [])):
            score += 2
        score += float(doctor.get("rating") or 0)
        scored.append({**doctor, "score": score})

    scored.sort(key=lambda doctor: float(doctor.get("score") or 0), reverse=True)
    return scored[:5]
