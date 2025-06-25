from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import Session

from app.modules.users.models.users import Profile
from app.modules.users.entities.profiles import CreateProfile, UpdateProfile


def get_profile_by_user_id(user_id: int, db: Session) -> Profile | None:
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    return profile


def get_profile_by_id(profile_id: int, db: Session) -> Profile | None:
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    return profile


def update_profile(user_data: UpdateProfile, db: Session) -> Profile:
    profile = get_profile_by_user_id(user_id=user_data['user_id'], db=db)
    if profile:
        for key, value in user_data.dict(exclude_unset=True).items():
            setattr(profile, key, value)
        db.commit()
        db.refresh(profile)
        return profile
    raise NoResultFound(detail='Profile not found')


def create_profile(user_data: CreateProfile, db: Session) -> Profile:
    new_profile = Profile(
        first_name=user_data['first_name'],
        last_name=user_data['last_name'],
        date_of_birth=user_data['date_of_birth'],
        email=user_data['email'],
        mobile_phone=user_data['mobile_phone'],
        avatar=user_data['avatar']
    )
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    return new_profile


def delete_profile_by_id(profile_id: int, db: Session) -> dict:
    profile = get_profile_by_id(profile_id, db)
    db.delete(profile)
    db.commit()
    return {'result': 'success', 'message': f'Профиль с ID {profile_id} удален'}
