from sqlalchemy.orm import Session

from ..models.users import  Profile
from ..entities.profiles import CreateProfile, UpdateProfile
from ..repository import profiles


def get_profile_by_user_id(user_id: int, db: Session) -> Profile | None:
    return profiles.get_profile_by_user_id(user_id, db)


def get_profile_by_id(profile_id: int, db: Session) -> Profile | None:
    return profiles.get_profile_by_id(profile_id, db)


def create_profile(user_data: CreateProfile, db: Session) -> Profile:
    return profiles.create_profile(user_data, db)


def update_profile(user_data: UpdateProfile, db: Session) -> Profile:
    return profiles.update_profile(user_data, db)


def delete_profile(profile_id: int, db: Session) -> dict:
    return profiles.delete_profile_by_id(profile_id, db)