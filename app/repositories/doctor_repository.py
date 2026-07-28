from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


class DoctorRepository:
    """Read-only JSON data access for doctor-related entities."""

    def __init__(self) -> None:
        base_dir = Path(__file__).resolve().parent.parent / "database"
        self._doctors_path = base_dir / "doctors.json"
        self._hospitals_path = base_dir / "hospitals.json"
        self._channeling_centers_path = base_dir / "channeling_centers.json"
        self._schedules_path = base_dir / "schedules.json"
        self._relationships_path = base_dir / "relationships"

        self._cache: dict[str, Any] = {}

    def _load_json_list(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists() or path.stat().st_size == 0:
            return []
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, list) else []

    def _load_relationship_map(self) -> dict[str, list[str]]:
        cached = self._cache.get("relationships")
        if cached is not None:
            return cached

        if not self._relationships_path.exists() or self._relationships_path.stat().st_size == 0:
            self._cache["relationships"] = {}
            return {}

        relationships: dict[str, list[str]] = {}
        for raw_line in self._relationships_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or ":" not in line:
                continue
            key, value = line.split(":", 1)
            related_ids = [item.strip() for item in value.split(",") if item.strip()]
            relationships[key.strip()] = related_ids

        self._cache["relationships"] = relationships
        return relationships

    def _get_cached_list(self, key: str, path: Path) -> list[dict[str, Any]]:
        if key not in self._cache:
            self._cache[key] = self._load_json_list(path)
        return self._cache[key]

    def get_all_doctors(self) -> list[dict[str, Any]]:
        return deepcopy(self._get_cached_list("doctors", self._doctors_path))

    def get_doctor_by_id(self, doctor_id: str) -> dict[str, Any] | None:
        for doctor in self._get_cached_list("doctors", self._doctors_path):
            if doctor.get("doctor_id") == doctor_id:
                return deepcopy(doctor)
        return None

    def get_doctors_by_ids(self, doctor_ids: list[str]) -> list[dict[str, Any]]:
        doctor_id_set = set(doctor_ids)
        return [
            deepcopy(doctor)
            for doctor in self._get_cached_list("doctors", self._doctors_path)
            if doctor.get("doctor_id") in doctor_id_set
        ]

    def get_all_hospitals(self) -> list[dict[str, Any]]:
        return deepcopy(self._get_cached_list("hospitals", self._hospitals_path))

    def get_hospital_by_id(self, hospital_id: str) -> dict[str, Any] | None:
        for hospital in self._get_cached_list("hospitals", self._hospitals_path):
            if hospital.get("hospital_id") == hospital_id:
                return deepcopy(hospital)
        return None

    def get_hospitals_by_ids(self, hospital_ids: list[str]) -> list[dict[str, Any]]:
        hospital_id_set = set(hospital_ids)
        return [
            deepcopy(hospital)
            for hospital in self._get_cached_list("hospitals", self._hospitals_path)
            if hospital.get("hospital_id") in hospital_id_set
        ]

    def get_all_channeling_centers(self) -> list[dict[str, Any]]:
        return deepcopy(self._get_cached_list("channeling_centers", self._channeling_centers_path))

    def get_channeling_center_by_id(self, channeling_id: str) -> dict[str, Any] | None:
        for center in self._get_cached_list("channeling_centers", self._channeling_centers_path):
            if center.get("channeling_id") == channeling_id:
                return deepcopy(center)
        return None

    def get_channeling_centers_by_ids(self, channeling_ids: list[str]) -> list[dict[str, Any]]:
        channeling_id_set = set(channeling_ids)
        return [
            deepcopy(center)
            for center in self._get_cached_list("channeling_centers", self._channeling_centers_path)
            if center.get("channeling_id") in channeling_id_set
        ]

    def get_schedules_by_doctor_id(self, doctor_id: str) -> list[dict[str, Any]]:
        return [
            deepcopy(schedule)
            for schedule in self._get_cached_list("schedules", self._schedules_path)
            if schedule.get("doctor_id") == doctor_id
        ]

    def get_all_schedules(self) -> list[dict[str, Any]]:
        return deepcopy(self._get_cached_list("schedules", self._schedules_path))

    def get_related_doctor_ids(self, doctor_id: str) -> list[str]:
        relationships = self._load_relationship_map()
        related_ids = relationships.get(doctor_id, [])
        return [doctor_id_value for doctor_id_value in related_ids if isinstance(doctor_id_value, str)]
