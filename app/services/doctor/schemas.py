from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class DoctorSearchRequest(BaseModel):
    query: str | None = None
    specialty: str | None = None
    hospital_id: str | None = None
    city: str | None = None
    gender: Literal["Male", "Female"] | None = None
    language: str | None = None
    min_fee: int | None = Field(default=None, ge=0)
    max_fee: int | None = Field(default=None, ge=0)
    min_experience: int | None = Field(default=None, ge=0)
    min_rating: float | None = Field(default=None, ge=0, le=5)
    accepting_new_patients: bool | None = None
    available_only: bool = True
    limit: int = Field(default=10, ge=1, le=50)

    @model_validator(mode="after")
    def validate_fee_range(self):
        if self.min_fee is not None and self.max_fee is not None and self.min_fee > self.max_fee:
            raise ValueError("min_fee cannot be greater than max_fee")
        return self


class DoctorSummary(BaseModel):
    doctor_id: str
    name: str
    specialization: str | None = None
    gender: str | None = None
    experience_years: int | None = None
    consultation_fee_lkr: int | None = None
    rating: float | None = None
    languages: list[str] = Field(default_factory=list)
    hospital_ids: list[str] = Field(default_factory=list)
    channeling_center_ids: list[str] = Field(default_factory=list)
    accepting_new_patients: bool | None = None
    score: float | None = None


class DoctorDetails(BaseModel):
    doctor: dict[str, Any]
    hospitals: list[dict[str, Any]] = Field(default_factory=list)
    channeling_centers: list[dict[str, Any]] = Field(default_factory=list)
    schedule: list[dict[str, Any]] = Field(default_factory=list)
    available_slots: list[dict[str, Any]] = Field(default_factory=list)
    similar_doctors: list[DoctorSummary] = Field(default_factory=list)


class AvailableSlot(BaseModel):
    schedule_id: str | None = None
    date: str
    day: str
    start_time: str
    end_time: str
    available: bool = True
    location_id: str | None = None
    location_type: str | None = None
    remaining_capacity: int | None = None


class DoctorSearchResponse(BaseModel):
    results: list[DoctorSummary] = Field(default_factory=list)
    total: int = 0
    applied_filters: dict[str, Any] = Field(default_factory=dict)
    message: str | None = None


class DoctorToolResponse(BaseModel):
    success: bool = True
    message: str | None = None
    data: Any = None
    error: str | None = None
