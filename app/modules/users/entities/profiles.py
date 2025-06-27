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
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class ProfileResponseSchema(BaseModel):
    id: int
    first_name: str
    last_name: str
    date_of_birth: str | None
    email: EmailStr | None
    mobile_phone: str | None
    avatar: str | None
    user_id: int

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def format_date(cls, v):
        if isinstance(v, (date, datetime)):
            return v.isoformat()
        return v


class CreateProfile(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date | None
    email: EmailStr | None
    mobile_phone: str | None
    avatar: str | None
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class UpdateProfile(BaseModel):
    id: int
    first_name: str | None
    last_name: str | None
    date_of_birth: date | None
    email: EmailStr | None
    mobile_phone: str | None
    user_id: int
    avatar: str | None

    model_config = ConfigDict(from_attributes=True)