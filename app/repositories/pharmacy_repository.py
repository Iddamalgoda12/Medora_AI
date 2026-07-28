from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


class PharmacyRepository:
    def __init__(self) -> None:
        self._path = Path(__file__).resolve().parent.parent / "database" / "pharmacies.json"
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

    def get_by_id(self, pharmacy_id: str) -> dict[str, Any] | None:
        for pharmacy in self._load():
            if pharmacy.get("pharmacy_id") == pharmacy_id:
                return deepcopy(pharmacy)
        return None

    def search(self, query: str | None = None, city: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
        query_l = (query or "").lower()
        city_l = (city or "").lower()
        results = []
        for pharmacy in self._load():
            blob = " ".join(str(pharmacy.get(field, "")) for field in ("name", "city", "address")).lower()
            if query_l and query_l not in blob:
                continue
            if city_l and city_l not in str(pharmacy.get("city", "")).lower():
                continue
            results.append(deepcopy(pharmacy))
            if len(results) >= limit:
                break
        return results
