from pydantic import BaseModel, Field
from datetime import datetime, date
from core.domain.entities import Gender


class CreatePersonDTO(BaseModel):
    """DTO для создания персоны"""
    first_name: str = Field(..., description="Имя")
    last_name: str = Field(..., description="Фамилия")
    middle_name: str | None = Field(None, description="Отчество")
    date_of_birth: date | None = Field(None, description="Дата рождения")
    date_of_death: date | None = Field(None, description="Дата смерти")
    gender: Gender = Field(None, description="Пол")
    biography: str | None = Field(None, description="Биография")


class UpdatePersonDTO(BaseModel):
    """DTO для обновления персоны"""
    first_name: str | None = Field(None, description="Имя")
    last_name: str | None = Field(None, description="Фамилия")
    middle_name: str | None = Field(None, description="Отчество")
    date_of_birth: date | None = Field(None, description="Дата рождения")
    date_of_death: date | None = Field(None, description="Дата смерти")
    gender: Gender | None = Field(None, description="Пол")
    biography: str | None = Field(None, description="Биография")


class PersonResponseDTO(BaseModel):
    """DTO для ответа с персоной"""
    id: int
    first_name: str
    last_name: str
    middle_name: str | None
    date_of_birth: date | None
    date_of_death: date | None
    gender: Gender | None
    biography: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
