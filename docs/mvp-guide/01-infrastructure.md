# 1. Инфраструктура и база данных

---

### MVP-INFRA-01 — Настройка проекта: структура папок, pyproject.toml, requirements

**Что уже есть в репозитории:** рабочий десктоп в корне (`main.py`, `gui.py`, `models.py`, `database.py`). Каталог `core/` может отсутствовать — его создаёте на фазе C.

**Что нужно сделать:**

1. **Создать структуру `core/...`** по [ARCHITECTURE.md](../ARCHITECTURE.md), все `__init__.py`, без циклических импортов.
2. **`pyproject.toml`** (или актуальный `requirements.txt`) — добавить `alembic`, `email-validator`, `passlib` и т.д. по плану.
3. **При разбиении requirements** — `requirements/base.txt` и др., если вводите такую раскладку.
4. **`conftest.py`** в корне — для pytest.

Схема полей БД и домена для примеров ниже — в **[00-schema-and-mapping.md](00-schema-and-mapping.md)**.

**Файлы:**
- `pyproject.toml` — обновить зависимости
- `requirements/base.txt`, `requirements/api.txt`, `requirements/desktop.txt` — синхронизировать
- `core/__init__.py` — убедиться в наличии

---

### MVP-INFRA-02 — SQLAlchemy модели: User, Person, Relationship

**Что нужно сделать:** перенести/дублировать ORM в `core/infrastructure/database/models/` с методами `to_domain()` / `from_domain()`, согласованными с **[00-schema-and-mapping.md](00-schema-and-mapping.md)** (имена `date_of_birth`, `person_id` / `person_id_related`).

```python path=core/infrastructure/database/models/base.py
from datetime import datetime, UTC
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
```

> **⚠️ Важно:** `datetime.utcnow()` удалён в Python 3.12+. Используйте `datetime.now(UTC)`.

```python path=core/infrastructure/database/models/user_model.py
from sqlalchemy import Column, Integer, String, Boolean
from core.infrastructure.database.models.base import Base, TimestampMixin
from core.domain.entities.user import User


class UserModel(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    def to_domain(self) -> User:
        return User(
            id=self.id,
            email=self.email,
            username=self.username,
            password_hash=self.password_hash,
            is_active=self.is_active,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, user: User) -> "UserModel":
        return cls(
            id=user.id,
            email=user.email,
            username=user.username,
            password_hash=user.password_hash,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
```

```python path=core/infrastructure/database/models/person_model.py
from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey
from core.infrastructure.database.models.base import Base, TimestampMixin
from core.domain.entities.person import Person, Gender


class PersonModel(Base, TimestampMixin):
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # До таблицы users: без FK. После MVP auth: ForeignKey("users.id").
    owner_id = Column(Integer, nullable=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    date_of_death = Column(Date, nullable=True)
    gender = Column(String(10), nullable=False)  # в домене лучше Gender | None — см. блок ниже
    biography = Column(Text, nullable=True)

    def to_domain(self) -> Person:
        return Person(
            id=self.id,
            owner_id=self.owner_id,
            first_name=self.first_name,
            last_name=self.last_name,
            middle_name=self.middle_name,
            date_of_birth=self.date_of_birth,
            date_of_death=self.date_of_death,
            gender=Gender(self.gender) if self.gender else None,
            biography=self.biography,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, person: Person) -> "PersonModel":
        return cls(
            id=person.id,
            owner_id=person.owner_id,
            first_name=person.first_name,
            last_name=person.last_name,
            middle_name=person.middle_name,
            date_of_birth=person.date_of_birth,
            date_of_death=person.date_of_death,
            gender=person.gender.value if person.gender else None,
            biography=person.biography,
        )
```

> **⚠️ Критично:** Доменная сущность `Person` объявляет `gender: Gender` (обязательное поле без `| None`).
> Но `CreatePersonDTO` допускает `gender=None`, а колонка БД — `nullable=True`.
> При `Person(gender=None)` — TypeError, т.к. `Gender` — Enum и не принимает `None`.
> **Решение:** нужно изменить доменную сущность `Person` — заменить `gender: Gender` на `gender: Gender | None`.
> Это единственное место, где доменный слой должен быть скорректирован ради реального MVP-сценария.

```python path=core/infrastructure/database/models/relationship_model.py
from sqlalchemy import Column, Integer, String, ForeignKey
from core.infrastructure.database.models.base import Base
from core.domain.entities.relationship import Relationship


class RelationshipModel(Base):
    """Совпадает с корневым legacy `models.Relationship`: без created_at на таблице связей."""

    __tablename__ = "relationships"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False)
    person_id_related = Column(Integer, ForeignKey("persons.id"), nullable=False)
    relationship_type = Column(String(100), nullable=False)

    def to_domain(self) -> Relationship:
        return Relationship(
            id=self.id,
            person_id=self.person_id,
            person_id_related=self.person_id_related,
            relationship_type=self.relationship_type,
        )

    @classmethod
    def from_domain(cls, rel: Relationship) -> "RelationshipModel":
        return cls(
            id=rel.id,
            person_id=rel.person_id,
            person_id_related=rel.person_id_related,
            relationship_type=rel.relationship_type,
        )
```

> **Домен `Relationship`:** поля `id`, `person_id`, `person_id_related`, `relationship_type: str` (или узкий StrEnum со значениями `father` / `mother` / …). См. **[00-schema-and-mapping.md](00-schema-and-mapping.md)**.

```python path=core/infrastructure/database/models/__init__.py
from core.infrastructure.database.models.base import Base
from core.infrastructure.database.models.user_model import UserModel
from core.infrastructure.database.models.person_model import PersonModel
from core.infrastructure.database.models.relationship_model import RelationshipModel

__all__ = [
    "Base",
    "UserModel",
    "PersonModel",
    "RelationshipModel",
]
```

**Ключевые моменты:**
- Имена колонок БД совпадают с доменом: `owner_id`, `date_of_birth`, `date_of_death`, `person_id`, `person_id_related` — см. **[00-schema-and-mapping.md](00-schema-and-mapping.md)**.
- `relationship_type` — строка (или enum со `.value`).
- `gender` — строка в БД, в домене `Gender | None` при необходимости.

---

### MVP-INFRA-03 — Alembic: инициализация, начальная миграция

**Что нужно сделать:**

1. `alembic init alembic` в корне проекта
2. В `alembic/env.py` — импортировать `Base` из `core.infrastructure.database.models` и установить `target_metadata = Base.metadata`
3. Настроить `sqlalchemy.url` из `core.infrastructure.config.settings`
4. `alembic revision --autogenerate -m "initial"`
5. `alembic upgrade head` — проверить создание таблиц

**Файлы:**
- `alembic.ini` — конфигурация
- `alembic/env.py` — связка с моделями
- `alembic/versions/xxx_initial.py` — автогенерированная миграция

> **⚠️ Важно для SQLite:** SQLite не поддерживает многие `ALTER TABLE` операции (добавление NOT NULL колонки без default, изменение типа колонки и т.д.). В `alembic/env.py` обязательно установите `render_as_batch=True`:
> ```python
> # В alembic/env.py, внутри run_migrations_online():
> with connectable.connect() as connection:
>     context.configure(
>         connection=connection,
>         target_metadata=target_metadata,
>         render_as_batch=True,  # ← Обязательно для SQLite!
>     )
> ```

---

### MVP-INFRA-04 — Реализация UserRepository (SQLAlchemy)

**Что уже есть:** `UserRepository` интерфейс в `core/domain/repositories/user_repository.py`

**Что нужно сделать:**

Создать **синхронную** реализацию (для Desktop/SQLite) и **асинхронную** (для API/PostgreSQL).

```python path=core/infrastructure/database/repositories/sqlalchemy_user_repository.py
from typing import Optional, List
from sqlalchemy.orm import Session
from core.domain.repositories.user_repository import UserRepository
from core.domain.entities.user import User
from core.infrastructure.database.models.user_model import UserModel


class SQLAlchemyUserRepository(UserRepository):
    """Синхронная SQLAlchemy реализация репозитория пользователей"""

    def __init__(self, db: Session):
        self._db = db

    def create(self, user: User) -> User:
        db_model = UserModel.from_domain(user)
        self._db.add(db_model)
        self._db.commit()
        self._db.refresh(db_model)
        return db_model.to_domain()

    def get_by_id(self, user_id: int) -> Optional[User]:
        db_model = self._db.query(UserModel).filter(UserModel.id == user_id).first()
        return db_model.to_domain() if db_model else None

    def get_by_email(self, email: str) -> Optional[User]:
        db_model = self._db.query(UserModel).filter(UserModel.email == email).first()
        return db_model.to_domain() if db_model else None

    def get_by_username(self, username: str) -> Optional[User]:
        db_model = self._db.query(UserModel).filter(UserModel.username == username).first()
        return db_model.to_domain() if db_model else None

    def update(self, user: User) -> User:
        db_model = self._db.query(UserModel).filter(UserModel.id == user.id).first()
        if not db_model:
            raise ValueError(f"User {user.id} not found")
        db_model.email = user.email
        db_model.username = user.username
        db_model.password_hash = user.password_hash
        db_model.is_active = user.is_active
        self._db.commit()
        self._db.refresh(db_model)
        return db_model.to_domain()

    def delete(self, user_id: int) -> bool:
        db_model = self._db.query(UserModel).filter(UserModel.id == user_id).first()
        if db_model:
            self._db.delete(db_model)
            self._db.commit()
            return True
        return False

    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        db_models = self._db.query(UserModel).offset(skip).limit(limit).all()
        return [model.to_domain() for model in db_models]
```

```python path=core/infrastructure/database/repositories/async_user_repository.py
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.domain.repositories.user_repository import UserRepository
from core.domain.entities.user import User
from core.infrastructure.database.models.user_model import UserModel


class AsyncUserRepository(UserRepository):
    """Асинхронная SQLAlchemy реализация репозитория пользователей"""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(self, user: User) -> User:
        db_model = UserModel.from_domain(user)
        self._db.add(db_model)
        await self._db.commit()
        await self._db.refresh(db_model)
        return db_model.to_domain()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self._db.execute(select(UserModel).where(UserModel.id == user_id))
        db_model = result.scalar_one_or_none()
        return db_model.to_domain() if db_model else None

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self._db.execute(select(UserModel).where(UserModel.email == email))
        db_model = result.scalar_one_or_none()
        return db_model.to_domain() if db_model else None

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self._db.execute(select(UserModel).where(UserModel.username == username))
        db_model = result.scalar_one_or_none()
        return db_model.to_domain() if db_model else None

    async def update(self, user: User) -> User:
        result = await self._db.execute(select(UserModel).where(UserModel.id == user.id))
        db_model = result.scalar_one_or_none()
        if not db_model:
            raise ValueError(f"User {user.id} not found")
        db_model.email = user.email
        db_model.username = user.username
        db_model.password_hash = user.password_hash
        db_model.is_active = user.is_active
        await self._db.commit()
        await self._db.refresh(db_model)
        return db_model.to_domain()

    async def delete(self, user_id: int) -> bool:
        result = await self._db.execute(select(UserModel).where(UserModel.id == user_id))
        db_model = result.scalar_one_or_none()
        if db_model:
            await self._db.delete(db_model)
            await self._db.commit()
            return True
        return False

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        result = await self._db.execute(select(UserModel).offset(skip).limit(limit))
        db_models = result.scalars().all()
        return [model.to_domain() for model in db_models]
```

**Ключевой момент:** Обе реализации делегируют интерфейсу `UserRepository` (ABC), UseCase не знает, какая реализация используется.

> **⚠️ Критично — sync/async конфликт:** ABC `UserRepository` определяет **синхронные** методы (`def create(...)`), а `AsyncUserRepository` объявляет `async def create(...)`. В Python `async def` и `def` — разные сигнатуры. Вызов синхронного метода на async-объекте вернёт coroutine вместо результата, что сломает все UseCase'ы.
>
> **Рекомендация для MVP:** Используйте **только синхронные** репозитории для обеих платформ. FastAPI может работать с sync-зависимостями через пул потоков. Async-репозитории — преждевременная оптимизация для MVP.
>
> Если async всё же нужен — создайте отдельный интерфейс `AsyncUserRepository` с `async` методами и отдельные async-UseCase'ы.

---

### MVP-INFRA-05 — Реализация PersonRepository (SQLAlchemy)

**Аналогично MVP-INFRA-04**, но для `PersonRepository`.

```python path=core/infrastructure/database/repositories/sqlalchemy_person_repository.py
from typing import Optional, List
from sqlalchemy.orm import Session
from core.domain.repositories.person_repository import PersonRepository
from core.domain.entities.person import Person
from core.infrastructure.database.models.person_model import PersonModel


class SQLAlchemyPersonRepository(PersonRepository):
    """Синхронная SQLAlchemy реализация репозитория персон"""

    def __init__(self, db: Session):
        self._db = db

    def create(self, person: Person) -> Person:
        db_model = PersonModel.from_domain(person)
        self._db.add(db_model)
        self._db.commit()
        self._db.refresh(db_model)
        return db_model.to_domain()

    def get_by_id(self, person_id: int) -> Optional[Person]:
        db_model = self._db.query(PersonModel).filter(PersonModel.id == person_id).first()
        return db_model.to_domain() if db_model else None

    def get_by_id_and_owner_id(self, person_id: int, user_id: int) -> Optional[Person]:
        db_model = (
            self._db.query(PersonModel)
            .filter(PersonModel.id == person_id, PersonModel.owner_id == user_id)
            .first()
        )
        return db_model.to_domain() if db_model else None

    def update(self, person: Person) -> Person:
        db_model = self._db.query(PersonModel).filter(PersonModel.id == person.id).first()
        if not db_model:
            raise ValueError(f"Person {person.id} not found")
        for field in ["owner_id", "first_name", "last_name", "middle_name",
                       "date_of_birth", "date_of_death", "gender", "biography"]:
            setattr(db_model, field, getattr(person, field))
        self._db.commit()
        self._db.refresh(db_model)
        return db_model.to_domain()

    def delete(self, person_id: int) -> bool:
        db_model = self._db.query(PersonModel).filter(PersonModel.id == person_id).first()
        if db_model:
            self._db.delete(db_model)
            self._db.commit()
            return True
        return False

    def get_all(self, owner_id: int | None = None, skip: int = 0, limit: int = 100) -> List[Person]:
        query = self._db.query(PersonModel)
        if owner_id is not None:
            query = query.filter(PersonModel.owner_id == owner_id)
        db_models = query.offset(skip).limit(limit).all()
        return [model.to_domain() for model in db_models]
```

> **⚠️ Исправления:**
> 1. `get_by_id_and_owner_id` возвращает `Optional[Person]`, а не `Person` — нужно исправить аннотацию в интерфейсе `PersonRepository` тоже.
> 2. `get_all()` теперь принимает `owner_id` — критично для изоляции данных пользователей. Без этого фильтра загрузятся ВСЕ персоны из БД.

```python path=core/infrastructure/database/repositories/async_person_repository.py
# Асинхронная реализация — аналогично async_user_repository.py
# Заменить UserModel → PersonModel, User → Person
# Добавить метод get_by_id_and_owner_id с async/await
```

**Ключевой метод:** `get_by_id_and_owner_id` — проверка владения, возвращает `Person` или `None`.

---

### MVP-INFRA-06 — Реализация RelationshipRepository (SQLAlchemy)

```python path=core/infrastructure/database/repositories/sqlalchemy_relationship_repository.py
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from core.domain.repositories.relationship_repository import RelationshipRepository
from core.domain.entities.relationship import Relationship
from core.infrastructure.database.models.relationship_model import RelationshipModel


class SQLAlchemyRelationshipRepository(RelationshipRepository):
    """Синхронная SQLAlchemy реализация репозитория связей"""

    def __init__(self, db: Session):
        self._db = db

    def create(self, relationship: Relationship) -> Relationship:
        db_model = RelationshipModel.from_domain(relationship)
        self._db.add(db_model)
        self._db.commit()
        self._db.refresh(db_model)
        return db_model.to_domain()

    def get_by_id(self, relationship_id: int) -> Optional[Relationship]:
        db_model = self._db.query(RelationshipModel).filter(
            RelationshipModel.id == relationship_id
        ).first()
        return db_model.to_domain() if db_model else None

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Relationship]:
        db_models = self._db.query(RelationshipModel).offset(skip).limit(limit).all()
        return [model.to_domain() for model in db_models]

    def update(self, relationship: Relationship) -> Relationship:
        db_model = self._db.query(RelationshipModel).filter(
            RelationshipModel.id == relationship.id
        ).first()
        if not db_model:
            raise ValueError(f"Relationship {relationship.id} not found")
        for field in ["person_id", "person_id_related", "relationship_type"]:
            setattr(db_model, field, getattr(relationship, field))
        self._db.commit()
        self._db.refresh(db_model)
        return db_model.to_domain()

    def delete(self, relationship_id: int) -> bool:
        db_model = self._db.query(RelationshipModel).filter(
            RelationshipModel.id == relationship_id
        ).first()
        if db_model:
            self._db.delete(db_model)
            self._db.commit()
            return True
        return False

    def get_by_person_id(self, person_id: int) -> List[Relationship]:
        """Все рёбра, где персона — субъект или второй конец."""
        db_models = (
            self._db.query(RelationshipModel)
            .filter(or_(
                RelationshipModel.person_id == person_id,
                RelationshipModel.person_id_related == person_id
            ))
            .all()
        )
        return [model.to_domain() for model in db_models]

    def get_by_type(
        self, person_id: int, relationship_type: str
    ) -> List[Relationship]:
        """Связи заданного типа, где персона участвует с любой стороны."""
        db_models = (
            self._db.query(RelationshipModel)
            .filter(
                or_(
                    RelationshipModel.person_id == person_id,
                    RelationshipModel.person_id_related == person_id
                ),
                RelationshipModel.relationship_type == relationship_type
            )
            .all()
        )
        return [model.to_domain() for model in db_models]
```

```python path=core/infrastructure/database/repositories/async_relationship_repository.py
# Асинхронная реализация — аналогично async_user_repository.py
# Заменить UserModel → RelationshipModel
# Добавить методы get_by_person_id и get_by_type с or_ фильтром
```

**Ключевые моменты:**
- `get_by_person_id` — `person_id == person_id OR person_id_related == person_id`
- Проверка дубликатов перед `create` — с учётом семантики `father`/`mother`/`child` (см. текущий `gui.py` и **00-schema-and-mapping.md**).

---

### MVP-INFRA-07 — Конфигурация БД (SQLite dev, PostgreSQL prod) + settings.py

**Что уже есть:** `core/infrastructure/config/settings.py` (только PostgreSQL), `core/infrastructure/database/config.py` (только sync PostgreSQL).

**Что нужно сделать:**

1. Обновить `settings.py` — добавить `DB_TYPE` (sqlite/postgres), параметры SQLite
2. Обновить `database/config.py` — добавить sync SQLite engine, async PostgreSQL engine, `get_sync_session()`, `get_async_session()`, `init_db()`

```python path=core/infrastructure/config/settings.py
import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения."""

    # Database type
    DB_TYPE: str = "sqlite"  # "sqlite" или "postgres"

    # SQLite settings
    SQLITE_DB_DIR: str = "~/Documents"
    SQLITE_DB_NAME: str = "family_tree.db"

    # PostgreSQL settings
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_USER: str = "family_tree_user"
    DB_PASSWORD: str = "your_password"
    DB_NAME: str = "family_tree_db"

    # Auth settings
    SECRET_KEY: str = "your-super-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 1

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


def get_settings() -> Settings:
    return Settings()
```

```python path=core/infrastructure/database/config.py
"""
Конфигурация базы данных и SQLAlchemy.

⚠️ Движки создаются лениво (при первом обращении), чтобы:
- не падать при отсутствии .env или невалидных настройках на старте модуля;
- не создавать async-движок, если async не нужен (Desktop);
- не создавать sync-движок, если sync не нужен (API-only).
"""
from pathlib import Path
from functools import lru_cache
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Session
from core.infrastructure.config.settings import Settings


@lru_cache
def _get_settings() -> Settings:
    """Ленивая загрузка настроек — не падает при импорте модуля без .env"""
    return Settings()


def _get_sync_url(settings: Settings) -> str:
    if settings.DB_TYPE.lower() == "sqlite":
        db_path = Path(settings.SQLITE_DB_DIR).expanduser() / settings.SQLITE_DB_NAME
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{db_path}"
    return (
        f"postgresql+psycopg2://{settings.DB_USER}:{settings.DB_PASSWORD}"
        f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )


def _get_async_url(settings: Settings) -> str:
    if settings.DB_TYPE.lower() == "sqlite":
        db_path = Path(settings.SQLITE_DB_DIR).expanduser() / settings.SQLITE_DB_NAME
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite+aiosqlite:///{db_path}"
    return (
        f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}"
        f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )


# Ленивые движки — создаются только при обращении
_sync_engine = None
_sync_session_local = None
_async_engine = None
_async_session_local = None


def _ensure_sync_engine():
    global _sync_engine, _sync_session_local
    if _sync_engine is None:
        s = _get_settings()
        _sync_engine = create_engine(
            _get_sync_url(s),
            echo=False,
            connect_args={"check_same_thread": False} if s.DB_TYPE.lower() == "sqlite" else {},
        )
        _sync_session_local = sessionmaker(autocommit=False, autoflush=False, bind=_sync_engine)


def _ensure_async_engine():
    global _async_engine, _async_session_local
    if _async_engine is None:
        s = _get_settings()
        _async_engine = create_async_engine(_get_async_url(s), echo=False)
        _async_session_local = sessionmaker(_async_engine, class_=AsyncSession, expire_on_commit=False)


def get_sync_session():
    """Получить синхронную сессию (для Desktop)"""
    _ensure_sync_engine()
    session = _sync_session_local()
    try:
        yield session
    finally:
        session.close()


async def get_async_session():
    """Получить асинхронную сессию (для API)"""
    _ensure_async_engine()
    async with _async_session_local() as session:
        try:
            yield session
        finally:
            await session.close()


def init_db():
    """Создать таблицы (для SQLite при первом запуске Desktop)"""
    _ensure_sync_engine()
    from core.infrastructure.database.models import Base as ModelsBase
    ModelsBase.metadata.create_all(bind=_sync_engine)
```

> **⚠️ Исправления:**
> 1. Убран дубликат `Base = DeclarativeBase()` — единственный `Base` находится в `core/infrastructure/database/models/base.py`.
> 2. `Settings` загружается лениво через `@lru_cache` — модуль не упадёт при отсутствии `.env`.
> 3. Движки создаются лениво — `asyncpg` не нужен для Desktop, `psycopg2` не нужен для чистого API.
> 4. `api/dependencies/database.py` нужно обновить: заменить `from core.infrastructure.database.config import get_db` на `from core.infrastructure.database.config import get_sync_session`.
