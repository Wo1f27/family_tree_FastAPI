from sqlalchemy.orm import Session

from app.modules.users.models.users import User
from app.modules.users.entities.users import CreateUser, UpdateUser
from app.modules.auth.auth import hash_password


def get_user_by_id(user_id: int, db: Session) -> User | None:
    user = db.query(User).filter(User.id == user_id).one_or_none()
    return user


def get_user_by_username(username: str, db: Session) -> User | None:
    user = db.query(User).filter(User.username == username).one_or_none()
    return user


def get_list_users(db: Session) -> list[User]:
    users = db.query(User).all()
    return users


def create_user(user_data: CreateUser, db: Session) -> User:
    new_user = User(username=user_data.username, password=hash_password(user_data.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def update_user_by_id(user_data: UpdateUser, db: Session) -> User | None:
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


def delete_user_by_id(user_id: int, db: Session) -> dict:
    user = get_user_by_id(user_id, db)
    db.delete(user)
    db.commit()
    return {'result': 'success', 'message': f'Пользователь с ID {user_id} удален'}
