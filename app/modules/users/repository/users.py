from sqlalchemy.orm import Session

from app.modules.users.models.users import User
from app.modules.users.entities.users import CreateUser, UpdateUser, UserBaseSchema, UserResponse
from app.modules.auth.auth import hash_password


def get_user_by_id(user_id: int, db: Session) -> UserResponse | None:
    user = db.query(User).filter(User.id == user_id).one_or_none()
    return user


def get_user_by_username(username: str, db: Session) -> UserResponse | None:
    user = db.query(User).filter(User.username == username).one_or_none()
    if user:
        return UserResponse.model_validate(user)
    return None


def get_list_users(db: Session) -> list[User]:
    users = db.query(User).all()
    return users


def create_user(user_data: CreateUser, db: Session) -> UserResponse:
    new_user = User(username=user_data.username, password=user_data.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    user = get_user_by_username(new_user.username, db)
    return user.model_validate(user)


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
