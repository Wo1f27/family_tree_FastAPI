from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from datetime import datetime, date


class ProfileBaseSchema(BaseModel):
    id: int
    first_name: str
    last_name: str
    date_of_birth: date | None
    email: EmailStr | None
    mobile_phone: str | None
    avatar: str | None

    model_config = ConfigDict(from_attributes=True)


class CreateProfile(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date | None
    email: EmailStr | None
    mobile_phone: str | None
    avatar: str | None

    model_config = ConfigDict(from_attributes=True)


class UpdateProfile(BaseModel):
    id: int
    first_name: str | None
    last_name: str | None
    date_of_birth: date | None
    email: EmailStr | None
    mobile_phone: str | None
    avatar: str | None

    model_config = ConfigDict(from_attributes=True)