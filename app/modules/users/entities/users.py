from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from datetime import datetime


class UserBaseSchema(BaseModel):
    id: int
    username: str
    password: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class UserResponse(BaseModel):
    id: int
    username: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class CreateUser(BaseModel):
    username: str
    password: str

    @field_validator('username', mode='after')
    def check_username_not_spaces(cls, username):
        if ' ' in username:
            raise ValueError('Логин не должен содержать пробелов')
        return username

    model_config = ConfigDict(from_attributes=True)


class UpdateUser(BaseModel):
    id: int
    username: str | None
    password: str | None

    @field_validator('username', mode='after')
    def check_username_not_spaces(cls, username):
        if ' ' in username:
            raise ValueError('Логин не должен содержать пробелов')
        return username

    model_config = ConfigDict(from_attributes=True)
