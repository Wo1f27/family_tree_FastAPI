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
from .models.users import User
from .entities.users import UserBaseSchema
from ..users.entities.users import CreateUser, UpdateUser
from .operators import users


router = APIRouter(prefix='/users', tags=['Users'])


@router.get('/')
def get_users(request: Request, db: Session = Depends(get_db)) -> list[UserBaseSchema]:
    response = users.get_list_users(db=db)
    return response


@router.get('/{user_id}/')
def get_user(request: Request, user_id: int, db: Session = Depends(get_db)) -> UserBaseSchema | None:
    response = users.get_user(user_id, db)
    return response


@router.post('/')
def add_user(request: Request, user_data: CreateUser, db: Session = Depends(get_db)) -> UserBaseSchema:
    response = users.create_user(user_data, db)
    return response


@router.patch('/{user_id}/')
def update_user(request: Request, user_data: UpdateUser, db: Session = Depends(get_db)) -> UserBaseSchema | None:
    response = users.update_user(user_data, db)
    return response


@router.delete('/{user_id}/')
def delete_user(request: Request, user_id: int, db: Session = Depends(get_db)) -> dict:
    response = users.delete_user(user_id, db)
    return response
