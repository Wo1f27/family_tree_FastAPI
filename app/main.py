from fastapi import FastAPI, Depends, Request
from fastapi.templating import Jinja2Templates
from app.modules.auth import auth_routers


app = FastAPI()

templates = Jinja2Templates(directory='templates/')

app.include_router(auth_routers.router, dependencies=[Depends(lambda: templates)])


@app.get('/')
def hello():
    return {'title': 'Hello on Family-Tree'}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app.main:app', reload=True)
