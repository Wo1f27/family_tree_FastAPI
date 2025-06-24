from fastapi import Depends
from sqlalchemy.orm import Session

from app.modules.users.models.users import User, Profile
from app.modules.users.entities.users import CreateUser, CreateProfile, UpdateUser
from app.db.config import get_db
from app.modules.auth.auth import hash_password


def get_user_by_id(user_id: int, db: Session = Depends(get_db)) -> User | None:
    user = db.query(User).filter(User.id == user_id).one_or_none()
    return user


def get_list_users(db: Session) -> list[User]:
    users = db.query(User).all()
    return users


def create_user(user_data: CreateUser, db: Session = Depends(get_db)) -> User:
    new_user = User(username=user_data.username, password=hash_password(user_data.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def update_user_by_id(user_data: UpdateUser, db: Session = Depends(get_db)) -> User | None:
    user = get_user_by_id(user_data.id, db)
    if user:
        if user_data.username:
            user.username = user_data.username
        if user_data.password:
            user.password = hash_password(user_data.password)
    else:
        return None
    db.commit()
    return user


def delete_user_by_id(user_id: int, db: Session = Depends(get_db)) -> dict:
    user = get_user_by_id(user_id, db)
    db.delete(user)
    db.commit()
    return {'result': 'success', 'message': f'Пользователь с ID {user_id} удален'}
