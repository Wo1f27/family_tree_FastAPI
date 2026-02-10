"""
Точка входа FastAPI приложения.
"""
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates

# TODO: Импортировать роуты после их создания
# from api.routes import auth, persons, users, relationships

app = FastAPI(
    title="Family Tree API",
    description="API для управления генеалогическим деревом",
    version="0.1.0"
)

# TODO: Подключить роуты
# app.include_router(auth.router)
# app.include_router(persons.router)
# app.include_router(users.router)
# app.include_router(relationships.router)

templates = Jinja2Templates(directory="app/templates")


@app.get("/")
def root():
    """Корневой эндпоинт."""
    return {"title": "Hello on Family-Tree API", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", reload=True)
