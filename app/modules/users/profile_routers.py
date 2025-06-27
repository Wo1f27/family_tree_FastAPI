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
from ..users.entities.profiles import CreateProfile, UpdateProfile, ProfileResponseSchema, ProfileBaseSchema
from .operators import profiles


router = APIRouter(prefix='/profile', tags=['Profile'])


@router.get('/{profile_id}/')
def get_profile(profile_id: int, db: Session = Depends(get_db)) -> JSONResponse:
    try:
        response = profiles.get_profile_by_id(profile_id, db)
        if response.get('success', False) is True:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=response
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=response
            )
    except Exception as e:
        print(f'Ошибка {e}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response
        )


@router.post('/')
def create_profile(user_data: CreateProfile, db: Session = Depends(get_db)) -> JSONResponse:
    try:
        response = profiles.create_profile(user_data, db)
        if response.get('success', False) is True:
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content=response
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=response
            )
    except Exception as e:
        print(f'Ошибка {e}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response
        )


@router.patch('/')
def update_profile(user_data: UpdateProfile, db: Session = Depends(get_db)) -> JSONResponse:
    try:
        response = profiles.update_profile(user_data, db)
        if response.get('success', False) is True:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=response
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=response
            )
    except Exception as e:
        print(f'Ошибка {e}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response
        )


@router.delete('/{profile_id}/')
def delete_profile(profile_id: int, db: Session = Depends(get_db)) -> JSONResponse:
    try:
        response = profiles.delete_profile(profile_id, db)
        if response.get('success'):
            return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content=response
                )
        else:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=response
            )
    except Exception as e:
        print(f'Ошибка {e}')
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=response
        )
