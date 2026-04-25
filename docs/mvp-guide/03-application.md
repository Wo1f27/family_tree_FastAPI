# 3. Application-слой (DTO, Use Cases)

---

### MVP-APP-01 — DTO: CreateUserDTO, UpdateUserDTO, AdminUpdateUserDTO, ResponseUserDTO

**Статус: ✅ Уже реализовано.** Файл `core/application/dto/user_dto.py` содержит все четыре DTO.

---

### MVP-APP-02 — DTO: CreatePersonDTO, UpdatePersonDTO, PersonResponseDTO

**Статус: ✅ Уже реализовано.** Файл `core/application/dto/person_dto.py` содержит все три DTO.

---

### MVP-APP-03 — DTO: CreateRelationshipDTO, RelationshipResponseDTO

**Что нужно сделать:**

```python path=core/application/dto/relationship_dto.py
from pydantic import BaseModel, Field, model_validator
from datetime import datetime
from core.domain.entities import RelationshipType


class CreateRelationshipDTO(BaseModel):
    person_1: int = Field(..., description="ID первой персоны")
    person_2: int = Field(..., description="ID второй персоны")
    relationship_type: RelationshipType = Field(..., description="Тип связи")
    start_date: datetime | None = None
    end_date: datetime | None = None

    @model_validator(mode="after")
    def validate_persons(self):
        if self.person_1 == self.person_2:
            raise ValueError("Персона не может быть связана сама с собой")
        return self


class RelationshipResponseDTO(BaseModel):
    id: int
    person_1: int
    person_2: int
    relationship_type: RelationshipType
    start_date: datetime | None
    end_date: datetime | None
    created_at: datetime
```

> **⚠️ Важно:** `start_date` и `end_date` — `datetime`, не `date`. Должно совпадать с доменной сущностью `Relationship`.

---

### MVP-APP-04 — DTO: AuthDTO (LoginDTO, TokenResponseDTO, ForgotPasswordDTO, ResetPasswordDTO)

**Что нужно сделать:**

```python path=core/application/dto/auth_dto.py
from pydantic import BaseModel, EmailStr, Field


class LoginDTO(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class TokenResponseDTO(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenDTO(BaseModel):
    refresh_token: str


class ForgotPasswordDTO(BaseModel):
    email: EmailStr


class ResetPasswordDTO(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)
```

---

### MVP-APP-05 — Use Case: CreateUserUseCase

**Статус: ✅ Уже реализовано.** Файл `core/application/use_cases/user/create_user.py`.

---

### MVP-APP-06 — Use Case: LoginUseCase

**Что нужно сделать:**

Сначала нужно создать интерфейсы сервисов в application-слое, чтобы не нарушать Dependency Rule:

```python path=core/application/interfaces/password_service.py
from abc import ABC, abstractmethod


class IPasswordService(ABC):
    """Интерфейс сервиса хеширования/проверки паролей"""

    @abstractmethod
    def hash_password(self, password: str) -> str:
        pass

    @abstractmethod
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        pass
```

```python path=core/application/interfaces/token_service.py
from abc import ABC, abstractmethod


class ITokenService(ABC):
    """Интерфейс сервиса JWT-токенов"""

    @abstractmethod
    def create_access_token(self, data: dict) -> str:
        pass

    @abstractmethod
    def create_refresh_token(self, data: dict) -> str:
        pass

    @abstractmethod
    def get_user_id_from_token(self, token: str) -> int:
        pass
```

```python path=core/infrastructure/auth/password_service_adapter.py
"""Адаптер: IPasswordService → bcrypt"""
from core.application.interfaces.password_service import IPasswordService
from core.infrastructure.auth.password_service import hash_password, verify_password


class BcryptPasswordService(IPasswordService):
    def hash_password(self, password: str) -> str:
        return hash_password(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return verify_password(plain_password, hashed_password)
```

```python path=core/infrastructure/auth/jwt_service_adapter.py
"""Адаптер: ITokenService → python-jose"""
from core.application.interfaces.token_service import ITokenService
from core.infrastructure.auth.jwt_service import create_access_token, create_refresh_token, get_user_id_from_token


class JoseTokenService(ITokenService):
    def create_access_token(self, data: dict) -> str:
        return create_access_token(data)

    def create_refresh_token(self, data: dict) -> str:
        return create_refresh_token(data)

    def get_user_id_from_token(self, token: str) -> int:
        return get_user_id_from_token(token)
```

Теперь LoginUseCase зависит только от интерфейсов application-слоя:

```python path=core/application/use_cases/user/login_user.py
from core.domain.repositories import UserRepository
from core.application.interfaces.password_service import IPasswordService
from core.application.interfaces.token_service import ITokenService
from core.application.dto.auth_dto import LoginDTO, TokenResponseDTO


class LoginUseCase:
    def __init__(
        self,
        user_repo: UserRepository,
        password_service: IPasswordService,
        token_service: ITokenService,
    ):
        self._user_repo = user_repo
        self._password_service = password_service
        self._token_service = token_service

    def execute(self, dto: LoginDTO) -> TokenResponseDTO:
        user = self._user_repo.get_by_email(dto.email)
        if not user:
            raise ValueError("Неверный email или пароль")
        if not self._password_service.verify_password(dto.password, user.password_hash):
            raise ValueError("Неверный email или пароль")
        if not user.is_active:
            raise ValueError("Аккаунт деактивирован")

        access = self._token_service.create_access_token({"sub": str(user.id)})
        refresh = self._token_service.create_refresh_token({"sub": str(user.id)})
        return TokenResponseDTO(access_token=access, refresh_token=refresh)
```

**Зависит от:** MVP-INFRA-08 (JWT-сервис).

> **⚠️ Критично — Dependency Rule:** Ранее LoginUseCase напрямую импортировал `core.infrastructure.auth.*`, нарушая правило зависимостей Clean Architecture (application НЕ зависит от infrastructure). Теперь зависимости внедряются через интерфейсы `IPasswordService` и `ITokenService`, которые находятся в `core/application/interfaces/`.
>
> Аналогичное исправление нужно для **существующего** `CreateUserUseCase` — он тоже импортирует `hash_password` из infrastructure.

---

### MVP-APP-07 — Use Case: UpdateUserUseCase

**Статус: ✅ Уже реализовано.** Файл `core/application/use_cases/user/update_user.py`. Проверяет уникальность email, username не меняется.

---

### MVP-APP-08 — Use Case: ChangePasswordUseCase

**Что нужно сделать:**

```python path=core/application/use_cases/user/change_password.py
from core.domain.repositories import UserRepository
from core.application.interfaces.password_service import IPasswordService


class ChangePasswordUseCase:
    def __init__(self, user_repo: UserRepository, password_service: IPasswordService):
        self._user_repo = user_repo
        self._password_service = password_service

    def execute(self, user_id: int, current_password: str, new_password: str) -> None:
        user = self._user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("Пользователь не найден")
        if not self._password_service.verify_password(current_password, user.password_hash):
            raise ValueError("Неверный текущий пароль")

        user.password_hash = self._password_service.hash_password(new_password)
        self._user_repo.update(user)
```

> **⚠️ Dependency Rule:** Использует `IPasswordService` вместо прямого импорта из infrastructure.

---

### MVP-APP-09 — Use Case: ForgotPasswordUseCase + ResetPasswordUseCase

**Что нужно сделать:**

```python path=core/application/use_cases/user/forgot_password.py
import secrets
from core.domain.repositories import UserRepository
from core.application.interfaces.password_service import IPasswordService
from core.infrastructure.services.email_service import IEmailService
from core.infrastructure.services.token_store import ResetTokenStore


class ForgotPasswordUseCase:
    def __init__(self, user_repo: UserRepository, email_service: IEmailService, token_store: ResetTokenStore):
        self._user_repo = user_repo
        self._email_service = email_service
        self._token_store = token_store

    def execute(self, email: str) -> str:
        """Возвращает токен сброса (для dev — логируется, для prod — отправляется по email)"""
        user = self._user_repo.get_by_email(email)
        if not user:
            # Не раскрываем, что email не существует
            return ""

        token = secrets.token_urlsafe(32)
        self._token_store.save(token, user.id, ttl_minutes=30)
        self._email_service.send_reset_email(email, token)
        return token


class ResetPasswordUseCase:
    def __init__(self, user_repo: UserRepository, token_store: ResetTokenStore, password_service: IPasswordService):
        self._user_repo = user_repo
        self._token_store = token_store
        self._password_service = password_service

    def execute(self, token: str, new_password: str) -> None:
        user_id = self._token_store.validate_token(token)
        if not user_id:
            raise ValueError("Недействительный или истёкший токен сброса")

        user = self._user_repo.get_by_id(user_id)
        user.password_hash = self._password_service.hash_password(new_password)
        self._user_repo.update(user)
        self._token_store.invalidate_token(token)
```

**Зависит от:** MVP-INFRA-09 (Email-сервис) + простое хранилище токенов.

> **⚠️ Dependency Rule:** `ForgotPasswordUseCase` и `ResetPasswordUseCase` теперь используют `IPasswordService` вместо прямого импорта из infrastructure.

---

### MVP-APP-10 — Use Case: CreatePersonUseCase

**Статус: ✅ Уже реализовано.** Файл `core/application/use_cases/person/create_person.py`.

---

### MVP-APP-11 — Use Case: GetPersonUseCase + GetAllPersonsUseCase

**Что уже есть:** `GetPersonUseCase` в `core/application/use_cases/person/get_person.py`.

**Что нужно добавить:**

```python path=core/application/use_cases/person/get_all_persons.py
from core.domain.entities import Person
from core.domain.repositories import PersonRepository


class GetAllPersonsUseCase:
    def __init__(self, person_repo: PersonRepository):
        self._person_repo = person_repo

    def execute(self, user_id: int, skip: int = 0, limit: int = 100) -> list[Person]:
        return self._person_repo.get_all(owner_id=user_id, skip=skip, limit=limit)
```

> **⚠️ Критично:** `PersonRepository.get_all()` теперь принимает `owner_id` — это исправлено в MVP-INFRA-05. Без этого фильтра загрузятся ВСЕ персоны из БД, включая чужие.

---

### MVP-APP-12 — Use Case: UpdatePersonUseCase

**Статус: ✅ Уже реализовано.** Файл `core/application/use_cases/person/update_person.py`.

---

### MVP-APP-13 — Use Case: DeletePersonUseCase

**Что нужно сделать:**

```python path=core/application/use_cases/person/delete_person.py
from core.domain.repositories import PersonRepository, RelationshipRepository


class DeletePersonUseCase:
    def __init__(self, person_repo: PersonRepository, rel_repo: RelationshipRepository):
        self._person_repo = person_repo
        self._rel_repo = rel_repo

    def execute(self, person_id: int, user_id: int) -> bool:
        # Проверка владения
        person = self._person_repo.get_by_id_and_owner_id(person_id, user_id)
        if not person:
            raise ValueError("Карточка не найдена")

        # Каскадное удаление всех связей + персоны в одной транзакции
        # Важно: оба репозитория должны использовать одну и ту же сессию БД
        relationships = self._rel_repo.get_by_person_id(person_id)
        for rel in relationships:
            self._rel_repo.delete(rel.id)

        return self._person_repo.delete(person_id)
```

> **⚠️ Транзакционность:** Оба репозитория должны использовать одну и ту же SQLAlchemy-сессию.
> Если удаление связи упадёт на середине, частично удалённые связи останутся.
> Для MVP — допустимо при условии общей сессии (commit происходит в `person_repo.delete()`).
> Для продакшена — вынести commit за пределы репозитория и управлять транзакцией в UseCase.

---

### MVP-APP-14 — Use Case: CreateRelationshipUseCase

**Что нужно сделать:**

```python path=core/application/use_cases/relationship/create_relationship.py
from core.domain.entities import Relationship, RelationshipType
from core.domain.repositories import PersonRepository, RelationshipRepository
from core.application.dto.relationship_dto import CreateRelationshipDTO


class CreateRelationshipUseCase:
    def __init__(self, person_repo: PersonRepository, rel_repo: RelationshipRepository):
        self._person_repo = person_repo
        self._rel_repo = rel_repo

    def execute(self, dto: CreateRelationshipDTO, user_id: int) -> Relationship:
        # Проверка владения обеими персонами
        p1 = self._person_repo.get_by_id_and_owner_id(dto.person_1, user_id)
        if not p1:
            raise ValueError("Персона 1 не найдена или не принадлежит вам")
        p2 = self._person_repo.get_by_id_and_owner_id(dto.person_2, user_id)
        if not p2:
            raise ValueError("Персона 2 не найдена или не принадлежит вам")

        # Проверка дубликата (оба направления)
        existing = self._rel_repo.get_by_person_id(dto.person_1)
        for rel in existing:
            # Прямой дубликат: A→B parent
            if (rel.person_1 == dto.person_1 and rel.person_2 == dto.person_2
                    and rel.relationship_type == dto.relationship_type):
                raise ValueError("Такая связь уже существует")
            # Обратный дубликат: B→A child (parent и child — одна и та же связь)
            if (rel.person_1 == dto.person_2 and rel.person_2 == dto.person_1
                    and rel.relationship_type == dto.relationship_type.get_reverse_type()
                    and dto.relationship_type in (RelationshipType.PARENT, RelationshipType.CHILD)):
                raise ValueError("Такая связь уже существует (в обратном направлении)")

        relationship = Relationship(
            id=None,
            person_1=dto.person_1,
            person_2=dto.person_2,
            relationship_type=dto.relationship_type,
            start_date=dto.start_date,
            end_date=dto.end_date,
        )
        return self._rel_repo.create(relationship)
```

> **⚠️ Исправлено:** Проверка дубликатов теперь ловит обратные связи (A→B parent + B→A child — логический дубликат).

---

### MVP-APP-15 — Use Case: GetRelationshipsUseCase + GetRelationshipsByTypeUseCase

```python path=core/application/use_cases/relationship/get_relationships.py
from core.domain.entities import Relationship, RelationshipType
from core.domain.repositories import RelationshipRepository


class GetRelationshipsUseCase:
    def __init__(self, rel_repo: RelationshipRepository):
        self._rel_repo = rel_repo

    def execute(self, person_id: int) -> list[Relationship]:
        return self._rel_repo.get_by_person_id(person_id)


class GetRelationshipsByTypeUseCase:
    def __init__(self, rel_repo: RelationshipRepository):
        self._rel_repo = rel_repo

    def execute(self, person_id: int, rel_type: RelationshipType) -> list[Relationship]:
        return self._rel_repo.get_by_type(person_id, rel_type)
```

---

### MVP-APP-16 — Use Case: DeleteRelationshipUseCase

```python path=core/application/use_cases/relationship/delete_relationship.py
from core.domain.repositories import RelationshipRepository, PersonRepository


class DeleteRelationshipUseCase:
    def __init__(self, rel_repo: RelationshipRepository, person_repo: PersonRepository):
        self._rel_repo = rel_repo
        self._person_repo = person_repo

    def execute(self, relationship_id: int, user_id: int) -> bool:
        rel = self._rel_repo.get_by_id(relationship_id)
        if not rel:
            raise ValueError("Связь не найдена")

        # Проверка владения хотя бы одной персоной в связи
        p1 = self._person_repo.get_by_id_and_owner_id(rel.person_1, user_id)
        p2 = self._person_repo.get_by_id_and_owner_id(rel.person_2, user_id)
        if not p1 and not p2:
            raise ValueError("Связь не принадлежит вам")

        return self._rel_repo.delete(relationship_id)
```

---

### MVP-APP-17 — Use Case: GetTreeDataUseCase

**Самый сложный Use Case.** BFS-обход от корня дерева.

```python path=core/application/use_cases/tree/get_tree_data.py
from collections import deque
from core.domain.entities import Person, Relationship, RelationshipType
from core.domain.repositories import PersonRepository, RelationshipRepository


class GetTreeDataUseCase:
    def __init__(self, person_repo: PersonRepository, rel_repo: RelationshipRepository):
        self._person_repo = person_repo
        self._rel_repo = rel_repo

    def execute(self, user_id: int) -> dict:
        """Возвращает {nodes, edges, generations} для визуализации"""
        persons = self._person_repo.get_all(owner_id=user_id)  # нужен owner_id фильтр
        if not persons:
            return {"nodes": [], "edges": [], "generations": []}

        # Собрать все связи
        all_relationships = []
        for p in persons:
            rels = self._rel_repo.get_by_person_id(p.id)
            all_relationships.extend(rels)

        # Уникализировать связи (т.к. get_by_person_id может вернуть дубли)
        seen = set()
        unique_rels = []
        for r in all_relationships:
            key = (min(r.person_1, r.person_2), max(r.person_1, r.person_2), r.relationship_type)
            if key not in seen:
                seen.add(key)
                unique_rels.append(r)

        # Найти корни (персоны без родителей)
        person_ids = {p.id for p in persons}
        has_parent = set()
        for r in unique_rels:
            if r.relationship_type == RelationshipType.PARENT:
                # person_1 — родитель, person_2 — ребёнок
                has_parent.add(r.person_2)

        roots = [p.id for p in persons if p.id not in has_parent]

        # BFS для назначения поколений
        generations = {}  # person_id → generation
        visited = set()
        queue = deque()

        for root_id in roots:
            generations[root_id] = 0
            queue.append(root_id)

        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)

            for r in unique_rels:
                if r.relationship_type == RelationshipType.PARENT:
                    if r.person_1 == current and r.person_2 not in visited:
                        generations[r.person_2] = generations.get(current, 0) + 1
                        queue.append(r.person_2)
                    elif r.person_2 == current and r.person_1 not in visited:
                        generations[r.person_1] = generations.get(current, 0) + 1
                        queue.append(r.person_1)

        # Персоны без поколения — назначить 0
        for p in persons:
            if p.id not in generations:
                generations[p.id] = 0

        # Формирование результата
        nodes = [
            {
                "id": p.id,
                "label": p.full_name,
                "gender": p.gender.value if p.gender else None,
                "is_alive": p.is_alive,
                "date_birth": str(p.date_birth) if p.date_birth else None,
                "date_death": str(p.date_death) if p.date_death else None,
                "generation": generations.get(p.id, 0),
            }
            for p in persons
        ]

        edges = [
            {
                "from": r.person_1,
                "to": r.person_2,
                "type": r.relationship_type.value,
            }
            for r in unique_rels
        ]

        max_gen = max(generations.values()) if generations else 0
        gen_list = [{"level": i, "label": f"Поколение {i}"} for i in range(max_gen + 1)]

        return {"nodes": nodes, "edges": edges, "generations": gen_list}
```
