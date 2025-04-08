from fastapi import APIRouter, HTTPException, Request
from fastapi.templating import Jinja2Templates


router = APIRouter(prefix='/login')
templates = Jinja2Templates(directory='app/templates')


@router.get('/')
def login_user(request: Request):
    return templates.TemplateResponse('login.html', {'request': request})
