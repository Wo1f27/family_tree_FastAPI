from datetime import datetime
from sqlalchemy.orm import Session

from ..models.users import  Profile
from ..entities.profiles import CreateProfile, UpdateProfile, ProfileBaseSchema, ProfileResponseSchema
from ..repository import profiles
from .users import get_user


def get_profile_by_user_id(user_id: int, db: Session) -> Profile | None:
    return profiles.get_profile_by_user_id(user_id, db)


def get_profile_by_id(profile_id: int, db: Session) -> dict:
    profile = profiles.get_profile_by_id(profile_id, db)
    if not profile:
        return {'success': False, 'detail': 'Профиль не найден'}
    if isinstance(profile.date_of_birth, datetime):
        profile.date_of_birth = profile.date_of_birth.isoformat()
    resp_profile = ProfileResponseSchema.model_validate(profile)
    resp_profile = resp_profile.model_dump()
    return {'success': True, 'detail': 'Профиль пользователя', 'profile': resp_profile}


def create_profile(user_data: CreateProfile, db: Session) -> dict:
    user = get_user(user_data.user_id, db)
    if not user:
        return {'success': False, 'detail': 'Пользователь не найден'}
    is_profile = get_profile_by_user_id(user_data.user_id, db)
    if is_profile:
        return {'success': False, 'detail': 'У пользователя уже есть профиль'}
    try:
        profile = profiles.create_profile(user_data, db)
        if isinstance(profile.date_of_birth, datetime):
            profile.date_of_birth = profile.date_of_birth.isoformat()
        resp_profile = ProfileResponseSchema.model_validate(profile)
        resp_profile = resp_profile.model_dump()
    except Exception as e:
        return {'success': False, 'detail': f'Ошибка при создании профиля: {e}'}
    return {'success': True, 'detail': 'Профиль создан успешно', 'profile': resp_profile}


def update_profile(user_data: UpdateProfile, db: Session) -> dict:
    try:
        profile = profiles.update_profile(user_data, db)
        if profile:
            if isinstance(profile.date_of_birth, datetime):
                profile.date_of_birth = profile.date_of_birth.isoformat()
            resp_profile = ProfileResponseSchema.model_validate(profile)
            resp_profile = resp_profile.model_dump()
    except Exception as e:
        return {'success': False, 'detail': f'Ошибка при изменении профиля: {e}'}
    return {'success': True, 'detail': 'Профиль изменен успешно', 'profile': resp_profile}


def delete_profile(profile_id: int, db: Session) -> dict:
    try:
        del_profile = profiles.delete_profile_by_id(profile_id, db)
        if del_profile['result'] == 'success':
            return {'success': True, 'detail': 'Профиль удален успешно'}
        else:
            return {'success': False, 'detail': 'Ошибка при удалении профиля'}
    except Exception as e:
        return {'success': False, 'detail': f'Ошибка при удалении профиля: {e}'}