from sqlalchemy.orm import Session
from ..models.users import User, Profile
from ..entities.users import CreateUser, UpdateUser, UserResponseSchema
from ..repository import users
from app.modules.auth.auth import hash_password


def get_user(user_id: int, db: Session) -> User | None:
    return users.get_user_by_id(user_id, db)


def get_user_by_username(username: str, db: Session) -> UserResponseSchema | None:
    return users.get_user_by_username(username, db)


def get_list_users(db: Session) -> list[User]:
    return users.get_list_users(db)


def create_user(data: CreateUser, db: Session) -> dict:
    try:
        user_dict = data.model_dump()
        user_dict['password'] = hash_password(data.password)
        user_dict = CreateUser(**user_dict)
        user = users.create_user(user_dict, db)
        resp_user = UserResponseSchema.model_validate(user)
        resp_user = resp_user.model_dump()
        return {'success': True, 'detail': 'Пользователь успешно создан', 'user': resp_user}
    except Exception as e:
        print(f'Ошибка при создании пользователя: {e}')
        return {'success': False, 'detail': f'Ошибка создания пользователя {e}'}



def update_user(data: UpdateUser, db: Session) -> User | None:
    return users.update_user_by_id(data, db)


def delete_user(user_id: int, db: Session) -> dict:
    return users.delete_user_by_id(user_id, db)
