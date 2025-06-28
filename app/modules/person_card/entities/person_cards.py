from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from datetime import date, datetime

from app.enums.enums import GenderEnum


class PersonCardBaseSchema(BaseModel):
    id: int
    first_name: str
    last_name: str
    patronymic: str | None
    date_of_birth: date | None
    date_of_death: date | None
    gender: int
    avatar: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class PersonCardCreateSchema(BaseModel):
    first_name: str
    last_name: str
    patronymic: str | None
    date_of_birth: date | None
    date_of_death: date | None
    gender: GenderEnum
    avatar: str | None

    model_config = ConfigDict(from_attributes=True)


class PersonCardUpdateSchema(BaseModel):
    first_name: str | None
    last_name: str | None
    patronymic: str | None
    date_of_birth: date | None
    date_of_death: date | None
    gender: int | None
    avatar: str | None

    model_config = ConfigDict(from_attributes=True)


class PersonCardResponseSchema(BaseModel):
    first_name: str | None
    last_name: str | None
    patronymic: str | None
    date_of_birth: str | None
    date_of_death: str | None
    gender: int | None
    avatar: str | None

    model_config = ConfigDict(from_attributes=True)


class KinshipCreateSchema(BaseModel):
    user_id: int
    root_id: int
    person_id: int
    kinship: int

    model_config = ConfigDict(from_attributes=True)


class KinshipUpdateSchema(BaseModel):
    root_id: int | None
    person_id: int | None
    kinship: int | None

    model_config = ConfigDict(from_attributes=True)


class PersonCardWithKinshipResponseSchema(BaseModel):
    first_name: str | None
    last_name: str | None
    patronymic: str | None
    date_of_birth: str | None
    date_of_death: str | None
    gender: int | None
    avatar: str | None
    kinship_persons: dict | None

    model_config = ConfigDict(from_attributes=True)