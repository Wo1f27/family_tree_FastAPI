from sqlalchemy.orm import Session
from ..models.users import User, Profile
from ..entities.users import CreateUser, CreateProfile, UpdateUser
from ..repository import users


def get_user(user_id: int, db: Session) -> User | None:
    return users.get_user_by_id(user_id, db)


def get_user_by_username(username: str, db: Session) -> User | None:
    return users.get_user_by_username(username, db)


def get_list_users(db: Session) -> list[User]:
    return users.get_list_users(db=db)


def create_user(data: CreateUser, db: Session) -> User:
    return users.create_user(data, db)


def update_user(data: UpdateUser, db: Session) -> User | None:
    return users.update_user_by_id(data, db)


def delete_user(user_id: int, db: Session) -> dict:
    return users.delete_user_by_id(user_id, db)
