# 5. Presentation-слой (Web API)

---

### MVP-API-01 — FastAPI app: роутер, middleware, CORS, exception handlers, lifespan

```python path=api/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from core.infrastructure.database.config import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown


app = FastAPI(
    title="Family Tree API",
    description="API для управления генеалогическим деревом",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В проде ограничить
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(PermissionError)
async def permission_error_handler(request: Request, exc: PermissionError):
    return JSONResponse(status_code=403, content={"detail": str(exc)})


# TODO: Подключить роуты после их создания
# from api.routes import auth, persons, users, relationships, tree
# app.include_router(auth.router)
# app.include_router(persons.router)
# app.include_router(users.router)
# app.include_router(relationships.router)
# app.include_router(tree.router)


@app.get("/")
def root():
    return {"title": "Family Tree API", "version": "0.1.0"}
```

---

### MVP-API-02 — Зависимость get_current_user (JWT-декодирование)

```python path=api/dependencies/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from core.infrastructure.auth.jwt_service import get_user_id_from_token
from core.domain.repositories import UserRepository
from api.dependencies.database import get_db_session
from core.infrastructure.database.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_db_session),
):
    """Извлекает user_id из JWT, загружает пользователя из БД"""
    try:
        user_id = get_user_id_from_token(credentials.credentials)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный или истёкший токен",
        )

    user_repo = SQLAlchemyUserRepository(db)
    user = user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
        )
    return user
```

---

### MVP-API-03 — Эндпоинты Auth: register, login, logout

```python path=api/routes/auth.py
from fastapi import APIRouter, Depends
from core.application.dto.auth_dto import LoginDTO, TokenResponseDTO, ForgotPasswordDTO, ResetPasswordDTO
from core.application.dto.user_dto import CreateUserDTO, ResponseUserDTO
from core.application.use_cases.user.create_user import CreateUserUseCase
from core.application.use_cases.user.login_user import LoginUseCase
from core.domain.entities import User
from api.dependencies.database import get_db_session
from api.dependencies.auth import get_current_user
from core.infrastructure.database.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", response_model=ResponseUserDTO, status_code=201)
def register(dto: CreateUserDTO, db=Depends(get_db_session)):
    user_repo = SQLAlchemyUserRepository(db)
    use_case = CreateUserUseCase(user_repo)
    user = use_case.execute(dto)
    return ResponseUserDTO(
        id=user.id,
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.post("/login", response_model=TokenResponseDTO)
def login(dto: LoginDTO, db=Depends(get_db_session)):
    user_repo = SQLAlchemyUserRepository(db)
    use_case = LoginUseCase(user_repo)
    return use_case.execute(dto)


@router.post("/logout")
def logout(user: User = Depends(get_current_user)):
    # Для MVP — просто 200 OK (инвалидация на клиенте)
    return {"message": "Успешный выход"}
```

---

### MVP-API-04 — Эндпоинты Auth: forgot-password, reset-password

```python path=api/routes/auth.py  # добавить в тот же роутер
from core.application.use_cases.user.forgot_password import ForgotPasswordUseCase, ResetPasswordUseCase
from core.infrastructure.services.email_service import DevEmailService
from core.infrastructure.services.token_store import ResetTokenStore

# Глобальный экземпляр (для MVP)
_token_store = ResetTokenStore()
_email_service = DevEmailService()


@router.post("/forgot-password")
def forgot_password(dto: ForgotPasswordDTO, db=Depends(get_db_session)):
    user_repo = SQLAlchemyUserRepository(db)
    use_case = ForgotPasswordUseCase(user_repo, _email_service, _token_store)
    use_case.execute(dto.email)
    return {"message": "Если email существует, письмо отправлено"}


@router.post("/reset-password")
def reset_password(dto: ResetPasswordDTO, db=Depends(get_db_session)):
    user_repo = SQLAlchemyUserRepository(db)
    use_case = ResetPasswordUseCase(user_repo, _token_store)
    use_case.execute(dto.token, dto.new_password)
    return {"message": "Пароль успешно сброшен"}
```

---

### MVP-API-05 — Эндпоинты Users: GET/PUT /me, PUT /me/password

```python path=api/routes/users.py
from fastapi import APIRouter, Depends
from core.application.dto.user_dto import UpdateUserDTO, ResponseUserDTO
from core.application.use_cases.user.update_user import UpdateUserUseCase
from core.application.use_cases.user.change_password import ChangePasswordUseCase
from core.domain.entities import User
from api.dependencies.database import get_db_session
from api.dependencies.auth import get_current_user
from core.infrastructure.database.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/me", response_model=ResponseUserDTO)
def get_me(user: User = Depends(get_current_user)):
    return ResponseUserDTO(
        id=user.id,
        email=user.email,
        username=user.username,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.put("/me", response_model=ResponseUserDTO)
def update_me(dto: UpdateUserDTO, user: User = Depends(get_current_user), db=Depends(get_db_session)):
    user_repo = SQLAlchemyUserRepository(db)
    use_case = UpdateUserUseCase(user_repo)
    updated = use_case.execute(dto, user.id)
    return ResponseUserDTO(
        id=updated.id,
        email=updated.email,
        username=updated.username,
        is_active=updated.is_active,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )


@router.put("/me/password")
def change_password(
    current_password: str,
    new_password: str,
    user: User = Depends(get_current_user),
    db=Depends(get_db_session),
):
    user_repo = SQLAlchemyUserRepository(db)
    use_case = ChangePasswordUseCase(user_repo)
    use_case.execute(user.id, current_password, new_password)
    return {"message": "Пароль успешно изменён"}
```

---

### MVP-API-06 — Эндпоинты Persons: CRUD + список с пагинацией

```python path=api/routes/persons.py
from fastapi import APIRouter, Depends, Query
from core.application.dto.person_dto import CreatePersonDTO, UpdatePersonDTO, PersonResponseDTO
from core.application.use_cases.person.create_person import CreatePersonUseCase
from core.application.use_cases.person.get_person import GetPersonUseCase
from core.application.use_cases.person.get_all_persons import GetAllPersonsUseCase
from core.application.use_cases.person.update_person import UpdatePersonUseCase
from core.application.use_cases.person.delete_person import DeletePersonUseCase
from core.domain.entities import User
from api.dependencies.database import get_db_session
from api.dependencies.auth import get_current_user
from core.infrastructure.database.repositories.sqlalchemy_person_repository import SQLAlchemyPersonRepository
from core.infrastructure.database.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository
from core.infrastructure.database.repositories.sqlalchemy_relationship_repository import SQLAlchemyRelationshipRepository

router = APIRouter(prefix="/api/persons", tags=["Persons"])


@router.post("/", response_model=PersonResponseDTO, status_code=201)
def create_person(dto: CreatePersonDTO, user: User = Depends(get_current_user), db=Depends(get_db_session)):
    person_repo = SQLAlchemyPersonRepository(db)
    user_repo = SQLAlchemyUserRepository(db)
    use_case = CreatePersonUseCase(person_repo, user_repo)
    person = use_case.execute(dto, user.id)
    return PersonResponseDTO(
        id=person.id,
        first_name=person.first_name,
        last_name=person.last_name,
        middle_name=person.middle_name,
        date_of_birth=person.date_of_birth,
        date_of_death=person.date_of_death,
        gender=person.gender,
        biography=person.biography,
        created_at=person.created_at,
        updated_at=person.updated_at,
    )


@router.get("/", response_model=list[PersonResponseDTO])
def get_persons(
    skip: int = Query(0), limit: int = Query(100),
    user: User = Depends(get_current_user), db=Depends(get_db_session),
):
    person_repo = SQLAlchemyPersonRepository(db)
    use_case = GetAllPersonsUseCase(person_repo)
    persons = use_case.execute(user.id, skip=skip, limit=limit)
    return [
        PersonResponseDTO(
            id=p.id, first_name=p.first_name, last_name=p.last_name,
            middle_name=p.middle_name, date_of_birth=p.date_of_birth,
            date_of_death=p.date_of_death, gender=p.gender, biography=p.biography,
            created_at=p.created_at, updated_at=p.updated_at,
        )
        for p in persons
    ]


@router.get("/{person_id}", response_model=PersonResponseDTO)
def get_person(person_id: int, user: User = Depends(get_current_user), db=Depends(get_db_session)):
    person_repo = SQLAlchemyPersonRepository(db)
    use_case = GetPersonUseCase(person_repo)
    person = use_case.execute(person_id, user.id)
    return PersonResponseDTO(
        id=person.id, first_name=person.first_name, last_name=person.last_name,
        middle_name=person.middle_name, date_of_birth=person.date_of_birth,
        date_of_death=person.date_of_death, gender=person.gender, biography=person.biography,
        created_at=person.created_at, updated_at=person.updated_at,
    )


@router.put("/{person_id}", response_model=PersonResponseDTO)
def update_person(
    person_id: int, dto: UpdatePersonDTO,
    user: User = Depends(get_current_user), db=Depends(get_db_session),
):
    dto.id = person_id
    person_repo = SQLAlchemyPersonRepository(db)
    use_case = UpdatePersonUseCase(person_repo)
    person = use_case.execute(dto, user.id)
    return PersonResponseDTO(
        id=person.id, first_name=person.first_name, last_name=person.last_name,
        middle_name=person.middle_name, date_of_birth=person.date_of_birth,
        date_of_death=person.date_of_death, gender=person.gender, biography=person.biography,
        created_at=person.created_at, updated_at=person.updated_at,
    )


@router.delete("/{person_id}", status_code=204)
def delete_person(person_id: int, user: User = Depends(get_current_user), db=Depends(get_db_session)):
    person_repo = SQLAlchemyPersonRepository(db)
    rel_repo = SQLAlchemyRelationshipRepository(db)
    use_case = DeletePersonUseCase(person_repo, rel_repo)
    use_case.execute(person_id, user.id)
```

---

### MVP-API-07 — Эндпоинты Relationships: CRUD + фильтрация

```python path=api/routes/relationships.py
from fastapi import APIRouter, Depends, Query
from core.application.dto.relationship_dto import CreateRelationshipDTO, RelationshipResponseDTO
from core.application.use_cases.relationship.create_relationship import CreateRelationshipUseCase
from core.application.use_cases.relationship.get_relationships import (
    GetRelationshipsUseCase, GetRelationshipsByTypeUseCase,
)
from core.application.use_cases.relationship.delete_relationship import DeleteRelationshipUseCase
from core.domain.entities import User, RelationshipType
from api.dependencies.database import get_db_session
from api.dependencies.auth import get_current_user
from core.infrastructure.database.repositories.sqlalchemy_person_repository import SQLAlchemyPersonRepository
from core.infrastructure.database.repositories.sqlalchemy_relationship_repository import SQLAlchemyRelationshipRepository

router = APIRouter(prefix="/api/relationships", tags=["Relationships"])


@router.post("/", response_model=RelationshipResponseDTO, status_code=201)
def create_relationship(dto: CreateRelationshipDTO, user: User = Depends(get_current_user), db=Depends(get_db_session)):
    person_repo = SQLAlchemyPersonRepository(db)
    rel_repo = SQLAlchemyRelationshipRepository(db)
    use_case = CreateRelationshipUseCase(person_repo, rel_repo)
    rel = use_case.execute(dto, user.id)
    return RelationshipResponseDTO(
        id=rel.id, person_id=rel.person_id, person_id_related=rel.person_id_related,
        relationship_type=rel.relationship_type, start_date=rel.start_date,
        end_date=rel.end_date, created_at=rel.created_at,
    )


@router.get("/", response_model=list[RelationshipResponseDTO])
def get_relationships(
    person_id: int = Query(None), rel_type: str = Query(None),
    user: User = Depends(get_current_user), db=Depends(get_db_session),
):
    rel_repo = SQLAlchemyRelationshipRepository(db)
    if rel_type:
        use_case = GetRelationshipsByTypeUseCase(rel_repo)
        rels = use_case.execute(person_id, RelationshipType(rel_type))
    else:
        use_case = GetRelationshipsUseCase(rel_repo)
        rels = use_case.execute(person_id)
    return [
        RelationshipResponseDTO(
            id=r.id, person_id=r.person_id, person_id_related=r.person_id_related,
            relationship_type=r.relationship_type, start_date=r.start_date,
            end_date=r.end_date, created_at=r.created_at,
        )
        for r in rels
    ]


@router.delete("/{relationship_id}", status_code=204)
def delete_relationship(
    relationship_id: int, user: User = Depends(get_current_user), db=Depends(get_db_session),
):
    person_repo = SQLAlchemyPersonRepository(db)
    rel_repo = SQLAlchemyRelationshipRepository(db)
    use_case = DeleteRelationshipUseCase(rel_repo, person_repo)
    use_case.execute(relationship_id, user.id)
```

---

### MVP-API-08 — Эндпоинт Tree: GET /api/tree

```python path=api/routes/tree.py
from fastapi import APIRouter, Depends
from core.application.use_cases.tree.get_tree_data import GetTreeDataUseCase
from core.domain.entities import User
from api.dependencies.database import get_db_session
from api.dependencies.auth import get_current_user
from core.infrastructure.database.repositories.sqlalchemy_person_repository import SQLAlchemyPersonRepository
from core.infrastructure.database.repositories.sqlalchemy_relationship_repository import SQLAlchemyRelationshipRepository

router = APIRouter(prefix="/api/tree", tags=["Tree"])


@router.get("/")
def get_tree(user: User = Depends(get_current_user), db=Depends(get_db_session)):
    person_repo = SQLAlchemyPersonRepository(db)
    rel_repo = SQLAlchemyRelationshipRepository(db)
    use_case = GetTreeDataUseCase(person_repo, rel_repo)
    return use_case.execute(user.id)
```
