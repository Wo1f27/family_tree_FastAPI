import json
from fastapi import (
    APIRouter,
    Depends,
    Request,
    Response,
    status
)
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from .auth import validate_user, hash_password
from app.db.config import get_db
from ..users.entities.users import CreateUser, UserResponse
from ..users.operators.users import create_user, get_user_by_username
from .jwt import create_access_token


router = APIRouter(prefix='/login', tags=['Auth'])
templates = Jinja2Templates(directory='templates/')


@router.get('/')
def login_user(request: Request):
    return templates.TemplateResponse('login.html', {'request': request})


@router.post('/', response_model=None)
async def auth_user(request: Request, response: Response, db: Session = Depends(get_db)):
    data = await request.body()
    body_str = data.decode('utf-8')
    data_json = json.loads(body_str)
    res = validate_user(db, data_json['username'], data_json['password'])
    if res.get('success'):
        user = UserResponse.model_validate(res['user'])
        payload = {
            'sub': str(user.id),
        }
        jwt_token = create_access_token(payload)
        # response.set_cookie(key='jwt', value=jwt_token, httponly=True)
        return JSONResponse(
            content={'token': jwt_token, 'message': 'Login successfully'},
            status_code=status.HTTP_200_OK
        )
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Invalid credentials"})


@router.post('/register/')
def register_user(user_data: CreateUser, db: Session = Depends(get_db)) -> JSONResponse:
    user = get_user_by_username(user_data.username, db)
    if user:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={'detail': 'Пользователь уже существует'}
        )
    user_dict = user_data.model_dump()
    user_dict['password'] = hash_password(user_data.password)
    user_dict = CreateUser(**user_dict)
    try:
        new_user = create_user(user_dict, db=db)
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={'success': False, 'detail': f'Непредвиденная ошибка сервера {e}'}
        )
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={'success': True, 'user': new_user.model_dump(), 'message': 'Вы успешно зарегистрированы!'}
    )
