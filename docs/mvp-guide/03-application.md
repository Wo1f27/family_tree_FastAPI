# 3. Application-слой (DTO, Use Cases)

---

### MVP-APP-01 — DTO: CreateUserDTO, UpdateUserDTO, AdminUpdateUserDTO, ResponseUserDTO

**Шаблон:** `core/application/dto/user_dto.py` — по мере внедрения auth (фаза D). Пока в корневом проекте может отсутствовать.

---

### MVP-APP-02 — DTO: CreatePersonDTO, UpdatePersonDTO, PersonResponseDTO

**Шаблон:** `core/application/dto/person_dto.py`. Поля дат — **`date_of_birth`**, **`date_of_death`**; при необходимости `owner_id` для веба. См. **[00-schema-and-mapping.md](00-schema-and-mapping.md)**.

---

### MVP-APP-03 — DTO: CreateRelationshipDTO, RelationshipResponseDTO

**Что нужно сделать:**

```python path=core/application/dto/relationship_dto.py
from pydantic import BaseModel, Field, model_validator


class CreateRelationshipDTO(BaseModel):
    """Направленное ребро: у person_id второй человек person_id_related с ролью relationship_type."""

    person_id: int = Field(..., description="Субъект связи (как в БД)")
    person_id_related: int = Field(..., description="Второй человек")
    relationship_type: str = Field(..., description="father|mother|child|spouse|sibling")

    @model_validator(mode="after")
    def validate_persons(self):
        if self.person_id == self.person_id_related:
            raise ValueError("Персона не может быть связана сама с собой")
        return self


class RelationshipResponseDTO(BaseModel):
    id: int
    person_id: int
    person_id_related: int
    relationship_type: str
```

> Семантика строк `relationship_type` и обратные связи — как в текущем `gui.py` и в **[00-schema-and-mapping.md](00-schema-and-mapping.md)**.

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

**Шаблон:** `core/application/use_cases/user/create_user.py` — при внедрении auth; в корневом репозитории может отсутствовать.

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

**Шаблон:** `core/application/use_cases/user/update_user.py`.

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

**Шаблон:** `core/application/use_cases/person/create_person.py` (поля дат — `date_of_birth` / `date_of_death`, см. **00-schema**).

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

**Шаблон:** `core/application/use_cases/person/update_person.py`.

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
from core.domain.entities import Relationship
from core.domain.repositories import PersonRepository, RelationshipRepository
from core.application.dto.relationship_dto import CreateRelationshipDTO


class CreateRelationshipUseCase:
    def __init__(self, person_repo: PersonRepository, rel_repo: RelationshipRepository):
        self._person_repo = person_repo
        self._rel_repo = rel_repo

    def execute(self, dto: CreateRelationshipDTO, user_id: int) -> Relationship:
        subj = self._person_repo.get_by_id_and_owner_id(dto.person_id, user_id)
        if not subj:
            raise ValueError("Субъект связи не найден или не принадлежит вам")
        other = self._person_repo.get_by_id_and_owner_id(dto.person_id_related, user_id)
        if not other:
            raise ValueError("Второй человек не найден или не принадлежит вам")

        # Проверка дубликата (прямой + эквиваленты father/mother ↔ child) — см. gui._has_equivalent_relationship
        existing = self._rel_repo.get_by_person_id(dto.person_id) + self._rel_repo.get_by_person_id(
            dto.person_id_related
        )
        for rel in existing:
            if (
                rel.person_id == dto.person_id
                and rel.person_id_related == dto.person_id_related
                and rel.relationship_type == dto.relationship_type
            ):
                raise ValueError("Такая связь уже существует")

        relationship = Relationship(
            id=None,
            person_id=dto.person_id,
            person_id_related=dto.person_id_related,
            relationship_type=dto.relationship_type,
        )
        return self._rel_repo.create(relationship)
```

> Дополните проверкой эквивалентных рёбер (`father`/`mother` vs `child`) по правилам из `gui.py`.

---

### MVP-APP-15 — Use Case: GetRelationshipsUseCase + GetRelationshipsByTypeUseCase

```python path=core/application/use_cases/relationship/get_relationships.py
from core.domain.entities import Relationship
from core.domain.repositories import RelationshipRepository


class GetRelationshipsUseCase:
    def __init__(self, rel_repo: RelationshipRepository):
        self._rel_repo = rel_repo

    def execute(self, person_id: int) -> list[Relationship]:
        return self._rel_repo.get_by_person_id(person_id)


class GetRelationshipsByTypeUseCase:
    def __init__(self, rel_repo: RelationshipRepository):
        self._rel_repo = rel_repo

    def execute(self, person_id: int, rel_type: str) -> list[Relationship]:
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

        # Проверка владения: хотя бы один конец ребра — «наш»
        a = self._person_repo.get_by_id_and_owner_id(rel.person_id, user_id)
        b = self._person_repo.get_by_id_and_owner_id(rel.person_id_related, user_id)
        if not a and not b:
            raise ValueError("Связь не принадлежит вам")

        return self._rel_repo.delete(relationship_id)
```

---

### MVP-APP-17 — Use Case: GetTreeDataUseCase

**Самый сложный Use Case.** BFS-обход от корня дерева.

```python path=core/application/use_cases/tree/get_tree_data.py
from collections import deque
from core.domain.entities import Person, Relationship
from core.domain.repositories import PersonRepository, RelationshipRepository


def _edge_key(r: Relationship) -> tuple[int, int, str]:
    """Уникальный ключ ребра для дедупликации при обходе списков per-person."""
    a, b = sorted((r.person_id, r.person_id_related))
    return (a, b, r.relationship_type)


class GetTreeDataUseCase:
    def __init__(self, person_repo: PersonRepository, rel_repo: RelationshipRepository):
        self._person_repo = person_repo
        self._rel_repo = rel_repo

    def execute(self, user_id: int) -> dict:
        """{nodes, edges, generations} — для vis.js / Canvas."""
        persons = self._person_repo.get_all(owner_id=user_id)
        if not persons:
            return {"nodes": [], "edges": [], "generations": []}

        all_relationships: list[Relationship] = []
        for p in persons:
            all_relationships.extend(self._rel_repo.get_by_person_id(p.id))

        seen: set[tuple[int, int, str]] = set()
        unique_rels: list[Relationship] = []
        for r in all_relationships:
            k = _edge_key(r)
            if k not in seen:
                seen.add(k)
                unique_rels.append(r)

        # «Есть родитель»: father/mother у ребёнка в person_id; или child у родителя в person_id
        person_ids = {p.id for p in persons}
        has_parent: set[int] = set()
        for r in unique_rels:
            if r.relationship_type in ("father", "mother"):
                has_parent.add(r.person_id)
            elif r.relationship_type == "child":
                has_parent.add(r.person_id_related)

        roots = [p.id for p in persons if p.id not in has_parent]

        generations: dict[int, int] = {}
        visited: set[int] = set()
        queue: deque[int] = deque()
        for root_id in roots:
            generations[root_id] = 0
            queue.append(root_id)

        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)

            for r in unique_rels:
                if r.relationship_type in ("father", "mother"):
                    child, parent = r.person_id, r.person_id_related
                    if parent == current and child not in visited:
                        generations[child] = generations.get(current, 0) + 1
                        queue.append(child)
                    elif child == current and parent not in visited:
                        generations[parent] = generations.get(current, 0) + 1
                        queue.append(parent)
                elif r.relationship_type == "child":
                    parent, child = r.person_id, r.person_id_related
                    if parent == current and child not in visited:
                        generations[child] = generations.get(current, 0) + 1
                        queue.append(child)
                    elif child == current and parent not in visited:
                        generations[parent] = generations.get(current, 0) + 1
                        queue.append(parent)

        for p in persons:
            if p.id not in generations:
                generations[p.id] = 0

        def label(p: Person) -> str:
            return f"{p.last_name} {p.first_name}".strip()

        nodes = [
            {
                "id": p.id,
                "label": label(p),
                "gender": p.gender.value if p.gender else None,
                "is_alive": p.date_of_death is None,
                "date_of_birth": str(p.date_of_birth) if p.date_of_birth else None,
                "date_of_death": str(p.date_of_death) if p.date_of_death else None,
                "generation": generations.get(p.id, 0),
            }
            for p in persons
        ]

        edges = [
            {
                "from": r.person_id,
                "to": r.person_id_related,
                "type": r.relationship_type,
            }
            for r in unique_rels
        ]

        max_gen = max(generations.values()) if generations else 0
        gen_list = [{"level": i, "label": f"Поколение {i}"} for i in range(max_gen + 1)]

        return {"nodes": nodes, "edges": edges, "generations": gen_list}
```
