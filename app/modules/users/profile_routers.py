from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status
)
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from sqlalchemy.orm import Session
from ..auth.auth import validate_user
from app.db.config import get_db
from ..users.models.users import Profile
from ..users.entities.profiles import ProfileBaseSchema
from ..users.entities.profiles import CreateProfile, UpdateProfile
from .operators import profiles


router = APIRouter(prefix='/profile', tags=['Profile'])


@router.get('/{profile_id}/')
def get_profile(profile_id: int, db: Session = Depends(get_db)) -> ProfileBaseSchema:
    response = profiles.get_profile_by_id(profile_id, db)
    return response


@router.post('/')
def create_profile(user_data: CreateProfile, db: Session = Depends(get_db)) -> ProfileBaseSchema:
    response = profiles.create_profile(user_data, db)
    return response


@router.patch('/{profile_id}/')
def update_profile(user_data: UpdateProfile, db: Session = Depends(get_db)) -> ProfileBaseSchema:
    response = profiles.update_profile(user_data, db)
    return response


@router.delete('/{profile_id}/')
def delete_profile(profile_id: int, db: Session = Depends(get_db)) -> dict:
    response = profiles.delete_profile(profile_id, db)
    return response
