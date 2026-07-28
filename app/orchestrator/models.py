from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class DoctorSearchInput(BaseModel):
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


class BookingInput(BaseModel):
    booking_id: str | None = None


class EmergencyInput(BaseModel):
    query: str


class DoctorResponse(BaseModel):
    success: bool = True
    message: str | None = None
    data: Any = None
    error: str | None = None


class BookingResponse(BaseModel):
    success: bool = True
    message: str | None = None
    data: Any = None
    error: str | None = None


class ToolResponse(BaseModel):
    success: bool = True
    message: str | None = None
    data: Any = None
    error: str | None = None
