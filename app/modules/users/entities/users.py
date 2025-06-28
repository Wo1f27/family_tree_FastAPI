from pydantic import BaseModel, field_validator, ConfigDict


class UserBaseSchema(BaseModel):
    id: int
    username: str
    password: str
    is_active: bool
    is_user: bool
    is_admin: bool
    is_superadmin: bool

    model_config = ConfigDict(
        from_attributes=True,
    )


class UserResponseSchema(BaseModel):
    id: int
    username: str
    is_active: bool
    is_user: bool
    is_admin: bool
    is_superadmin: bool

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
