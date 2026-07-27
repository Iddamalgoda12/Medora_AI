from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any

from app.repositories.doctor_repository import DoctorRepository
from app.services.doctor.availability import filter_available, get_available_slots
from app.services.doctor.ranking import find_similar_doctors, rank_doctors
from app.services.doctor.schemas import DoctorDetails, DoctorSearchRequest, DoctorSearchResponse, DoctorSummary


class DoctorService:
    def __init__(self, repository: DoctorRepository | None = None) -> None:
        self.repository = repository or DoctorRepository()

    def get_all_doctors(self) -> list[dict[str, Any]]:
        return self.repository.get_all_doctors()

    def get_doctor(self, doctor_id: str) -> dict[str, Any] | None:
        return self.repository.get_doctor_by_id(doctor_id)

    def _normalize_search_request(self, search_request: DoctorSearchRequest | dict[str, Any]) -> DoctorSearchRequest:
        if isinstance(search_request, DoctorSearchRequest):
            return search_request
        return DoctorSearchRequest.model_validate(search_request)

    def _build_doctor_lookup(self, schedules: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        lookup: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for schedule in schedules:
            date_value = str(schedule.get("date") or "")
            if date_value and date_value < date.today().isoformat():
                continue
            lookup[str(schedule.get("doctor_id") or "")].append(schedule)
        return lookup

    def _matches_filters(self, doctor: dict[str, Any], request: DoctorSearchRequest, schedules_by_doctor: dict[str, list[dict[str, Any]]]) -> bool:
        search_blob = " ".join(
            filter(
                None,
                [
                    str(doctor.get("name") or ""),
                    str(doctor.get("specialization") or ""),
                    " ".join(doctor.get("languages") or []),
                    " ".join(str(hospital_id) for hospital_id in doctor.get("hospital_ids") or []),
                    str(doctor.get("gender") or ""),
                ],
            )
        ).lower()

        if request.query and request.query.lower() not in search_blob:
            return False
        if request.specialty and request.specialty.lower() not in str(doctor.get("specialization") or "").lower():
            return False
        if request.gender and doctor.get("gender") != request.gender:
            return False
        if request.language and request.language.lower() not in [language.lower() for language in doctor.get("languages") or []]:
            return False
        if request.hospital_id and request.hospital_id not in set(doctor.get("hospital_ids") or []):
            return False
        if request.city:
            hospitals = self.repository.get_hospitals_by_ids(list(doctor.get("hospital_ids") or []))
            if not any(request.city.lower() in str(hospital.get("city") or "").lower() for hospital in hospitals):
                return False
        fee = int(doctor.get("consultation_fee_lkr") or 0)
        if request.min_fee is not None and fee < request.min_fee:
            return False
        if request.max_fee is not None and fee > request.max_fee:
            return False
        if request.min_experience is not None and int(doctor.get("experience_years") or 0) < request.min_experience:
            return False
        if request.min_rating is not None and float(doctor.get("rating") or 0) < request.min_rating:
            return False
        if request.accepting_new_patients is not None and bool(doctor.get("accepting_new_patients")) != request.accepting_new_patients:
            return False
        if request.available_only and not any(slot.get("status") == "available" for slot in schedules_by_doctor.get(str(doctor.get("doctor_id") or ""), [])):
            return False
        return True

    def search_doctors(self, search_request: DoctorSearchRequest | dict[str, Any]) -> DoctorSearchResponse:
        request = self._normalize_search_request(search_request)
        doctors = self.repository.get_all_doctors()
        schedules = self.repository.get_all_schedules()
        schedules_by_doctor = self._build_doctor_lookup(schedules)

        filtered = [doctor for doctor in doctors if self._matches_filters(doctor, request, schedules_by_doctor)]
        filtered = filter_available(filtered, request.model_dump(), schedules_by_doctor)
        ranked = rank_doctors(filtered, request.model_dump(), schedules_by_doctor)
        ranked = ranked[: request.limit]

        return DoctorSearchResponse(
            results=[DoctorSummary.model_validate(doctor) for doctor in ranked],
            total=len(ranked),
            applied_filters=request.model_dump(exclude_none=True),
            message="Doctors matched successfully" if ranked else "No doctors matched the current filters",
        )

    def get_doctor_details(self, doctor_id: str) -> DoctorDetails | None:
        doctor = self.repository.get_doctor_by_id(doctor_id)
        if not doctor:
            return None

        hospitals = self.repository.get_hospitals_by_ids(list(doctor.get("hospital_ids") or []))
        channeling_centers = self.repository.get_channeling_centers_by_ids(list(doctor.get("channeling_center_ids") or []))
        schedules = self.repository.get_schedules_by_doctor_id(doctor_id)
        available_slots = get_available_slots(schedules)
        similar_doctors = self.find_similar_doctors(doctor_id)

        return DoctorDetails(
            doctor=doctor,
            hospitals=hospitals,
            channeling_centers=channeling_centers,
            schedule=schedules,
            available_slots=available_slots,
            similar_doctors=[DoctorSummary.model_validate(item) for item in similar_doctors],
        )

    def get_available_slots(self, doctor_id: str) -> list[dict[str, Any]]:
        schedules = self.repository.get_schedules_by_doctor_id(doctor_id)
        return get_available_slots(schedules)

    def find_similar_doctors(self, doctor_id: str) -> list[dict[str, Any]]:
        doctor = self.repository.get_doctor_by_id(doctor_id)
        if not doctor:
            return []
        doctors = self.repository.get_all_doctors()
        return find_similar_doctors(doctor, doctors)
