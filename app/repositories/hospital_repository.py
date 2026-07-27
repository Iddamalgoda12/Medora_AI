from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


class HospitalRepository:
    def __init__(self) -> None:
        self._path = Path(__file__).resolve().parent.parent / "database" / "hospitals.json"
        self._cache: list[dict[str, Any]] | None = None

    def _load(self) -> list[dict[str, Any]]:
        if self._cache is None:
            if not self._path.exists() or self._path.stat().st_size == 0:
                self._cache = []
            else:
                self._cache = json.loads(self._path.read_text(encoding="utf-8"))
        return self._cache

    def get_all(self) -> list[dict[str, Any]]:
        return deepcopy(self._load())

    def get_by_id(self, hospital_id: str) -> dict[str, Any] | None:
        for hospital in self._load():
            if hospital.get("hospital_id") == hospital_id:
                return deepcopy(hospital)
        return None

    def search(self, query: str | None = None, city: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
        query_l = (query or "").lower()
        city_l = (city or "").lower()
        results = []
        for hospital in self._load():
            blob = " ".join(str(hospital.get(field, "")) for field in ("name", "city", "address")).lower()
            if query_l and query_l not in blob:
                continue
            if city_l and city_l not in str(hospital.get("city", "")).lower():
                continue
            results.append(deepcopy(hospital))
            if len(results) >= limit:
                break
        return results

    def save(self, hospitals: list[dict[str, Any]]) -> None:
        self._path.write_text(json.dumps(hospitals, indent=2, ensure_ascii=False), encoding="utf-8")
        self._cache = deepcopy(hospitals)
