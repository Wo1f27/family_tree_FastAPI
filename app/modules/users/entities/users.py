from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime


class CreateUser(BaseModel):
    username: str
    password: str

    @field_validator('username', mode='after')
    def check_username_not_spaces(self, username):
        if ' ' in username:
            raise ValueError('Логин не должен содержать пробелов')
        return username


class CreateProfile(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    email: EmailStr
    date_of_birth: datetime | None
    mobile_phone: str | None
    avatar: str | None
