"""Pydantic schemas for Person API."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class PersonBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    maiden_name: Optional[str] = Field(None, max_length=100)
    gender: str = Field(..., pattern="^(male|female|other)$")
    birth_year: Optional[int] = Field(None, ge=1, le=9999)
    birth_month: Optional[int] = Field(None, ge=1, le=12)
    birth_day: Optional[int] = Field(None, ge=1, le=31)
    birth_approx: bool = False
    death_year: Optional[int] = Field(None, ge=1, le=9999)
    death_month: Optional[int] = Field(None, ge=1, le=12)
    death_day: Optional[int] = Field(None, ge=1, le=31)
    death_approx: bool = False
    place_of_birth: Optional[str] = Field(None, max_length=255)
    place_of_death: Optional[str] = Field(None, max_length=255)
    burial_place: Optional[str] = Field(None, max_length=255)
    death_cause: Optional[str] = Field(None, pattern="^(natural|illness|other|unknown)$")
    biography: Optional[str] = None
    archive_records: Optional[str] = None


class PersonCreate(PersonBase):
    pass


class PersonUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    maiden_name: Optional[str] = Field(None, max_length=100)
    gender: Optional[str] = Field(None, pattern="^(male|female|other)$")
    birth_year: Optional[int] = Field(None, ge=1, le=9999)
    birth_month: Optional[int] = Field(None, ge=1, le=12)
    birth_day: Optional[int] = Field(None, ge=1, le=31)
    birth_approx: Optional[bool] = None
    death_year: Optional[int] = Field(None, ge=1, le=9999)
    death_month: Optional[int] = Field(None, ge=1, le=12)
    death_day: Optional[int] = Field(None, ge=1, le=31)
    death_approx: Optional[bool] = None
    place_of_birth: Optional[str] = Field(None, max_length=255)
    place_of_death: Optional[str] = Field(None, max_length=255)
    burial_place: Optional[str] = Field(None, max_length=255)
    death_cause: Optional[str] = Field(None, pattern="^(natural|illness|other|unknown)$")
    biography: Optional[str] = None
    archive_records: Optional[str] = None


class PersonResponse(PersonBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
