from fastapi import FastAPI, Depends, Request
from fastapi.templating import Jinja2Templates
from backend.app.modules import auth_routers
from backend.app.modules import user_routers, profile_routers
from backend.app.modules import person_cards_routers


app = FastAPI()

templates = Jinja2Templates(directory='templates/')

app.include_router(auth_routers.router)
app.include_router(user_routers.router)
app.include_router(profile_routers.router)
app.include_router(person_cards_routers.router)


@app.get('/')
def hello():
    return {'title': 'Hello on Family-Tree'}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app.main:app', reload=True)
