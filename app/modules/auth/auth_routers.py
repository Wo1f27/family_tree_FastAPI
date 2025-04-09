from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status
)
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from .auth import validate_user
from app.db.config import get_db


router = APIRouter(prefix='/login')
templates = Jinja2Templates(directory='app/templates')


@router.get('/')
def login_user(request: Request):
    return templates.TemplateResponse('login.html', {'request': request})


@router.post('/', response_model=None)
async def auth_user(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    res = validate_user(db, form.get('username'), form.get('password'))
    if res.get('success'):
        return RedirectResponse(url='/', status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(url='/login?error=Invalid credentials', status_code=status.HTTP_401_UNAUTHORIZED)
