"""Pydantic schemas for Photo API."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PhotoBase(BaseModel):
    original_filename: str = Field(..., max_length=255)
    mime_type: str = Field(..., pattern=r'^image/(jpeg|jpg|png|webp|gif|bmp)$')
    width: int = Field(..., gt=0)
    height: int = Field(..., gt=0)
    file_size: int = Field(..., ge=0)
    sort_order: int = Field(default=0)


class PhotoResponse(PhotoBase):
    id: int
    filename: str
    person_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PhotoCreate(BaseModel):
    """Схема для привязки существующего фото к персоне."""
    photo_id: int
    person_id: int


class PhotoDeleteResponse(BaseModel):
    deleted: bool
    filename: str
