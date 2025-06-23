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
from ..users.entities.users import CreateUser, UpdateUser
from .operators import users


router = APIRouter(prefix='/users', tags=['Users'])


@router.get('/')
def get_users(request: Request):
    response = users.get_list_users()
    return response


@router.get('/{user_id}/')
def get_user(request: Request, user_id: int):
    response = users.get_user(user_id)
    return response
