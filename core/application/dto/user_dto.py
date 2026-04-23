from pydantic import BaseModel, Field, EmailStr
from datetime import datetime


class CreateUserDTO(BaseModel):
    """DTO для создания пользователя"""
    username: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=8, max_length=64)
    email: EmailStr = Field(..., min_length=5, max_length=100)


class UpdateUserDTO(BaseModel):
    """DTO для обновления пользователя"""
    email: EmailStr = Field(None, min_length=5, max_length=100)


class AdminUpdateUserDTO(UpdateUserDTO):
    """DTO для обновления пользователя с правами администратора"""
    is_active: bool = Field(None)


class ResponseUserDTO(BaseModel):
    """DTO для ответа с пользователем"""
    id: int
    email: EmailStr
    is_active: bool
    username: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
