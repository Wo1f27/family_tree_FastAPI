from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status
)
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from sqlalchemy.orm import Session
from .auth import validate_user, hash_password
from app.db.config import get_db
from ..users.entities.users import CreateUser
from ..users.models.users import User
from ..users.operators.users import create_user, get_user_by_username
from jwt import create_access_token


router = APIRouter(prefix='/login', tags=['Auth'])
templates = Jinja2Templates(directory='templates/')


@router.get('/')
def login_user(request: Request):
    return templates.TemplateResponse('login.html', {'request': request})


@router.post('/', response_model=None)
async def auth_user(request: Request, response: Response, db: Session = Depends(get_db)):
    form = await request.form()
    res = validate_user(db, form.get('username'), form.get('password'))
    if res.get('success'):
        # user = db.query(User).filter(User.username == form.get('username')).first()
        user = res.get('user')
        payload = {
            'sub': str(user['id']),
        }
        jwt_token = create_access_token(payload)
        response.set_cookie(key='jwt', value=jwt_token, httponly=True)
        # return RedirectResponse(url=f'localhost/profile/{user['id']}', status_code=status.HTTP_303_SEE_OTHER)
        return JSONResponse(
            content={'token': jwt_token, 'message': 'Login successfully'},
            status_code=status.HTTP_200_OK
        )
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid credentials")


@router.post('/register/')
async def register_user(user_data: CreateUser, db: Session = Depends(get_db)) -> dict:
    user = get_user_by_username(user_data.username, db)
    if user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Пользователь уже существует')
    user_dict = user_data.dict()
    user_dict['password'] = hash_password(user_data.password)
    new_user = create_user(**user_dict, db=db)
    return {'success': True, 'user': new_user, 'message': 'Вы успешно зарегистрированы!'}
