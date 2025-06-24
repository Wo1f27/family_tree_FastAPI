from sqlalchemy.orm import Session
from ..models.users import User, Profile
from ..entities.users import CreateUser, CreateProfile, UpdateUser
from ..repository import users


def get_user(user_id: int) -> User | None:
    return users.get_user_by_id(user_id)


def get_list_users(db: Session) -> list[User]:
    return users.get_list_users(db=db)


def create_user(data: CreateUser) -> User:
    return users.create_user(data)


def update_user(data: UpdateUser) -> User | None:
    return users.update_user_by_id(data)


def delete_user(user_id: int) -> dict:
    return users.delete_user_by_id(user_id)
