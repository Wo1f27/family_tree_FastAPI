# Полная реализация: SQLite (Desktop) + PostgreSQL (Web)

## Архитектура

```
┌─────────────────────────────────────────────────────┐
│                 ЯДРО (core)                          │
│                                                      │
│  UseCase → IRepository (абстрактный интерфейс)       │
│         ↓                                            │
│  Domain Entity (User, Person, Relationship)          │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ↓                     ↓
┌───────────────┐    ┌───────────────┐
│  PostgreSQL   │    │    SQLite     │
│  (Web/API)    │    │  (Desktop)    │
│               │    │               │
│  asyncpg      │    │  sqlite3      │
└───────────────┘    └───────────────┘
```

---

## Шаг 1: Доменные сущности (Domain Entities)

### `core/domain/entities/user.py`

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """Доменная сущность пользователя"""
    id: Optional[int]
    email: str
    username: str
    password_hash: str
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if "@" not in self.email:
            raise ValueError("Некорректный email")
        if len(self.username) < 2:
            raise ValueError("Username минимум 2 символа")

    @property
    def is_authenticated(self) -> bool:
        return self.is_active
```

### `core/domain/entities/person.py`

```python
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class Person:
    """Доменная сущность персоны"""
    id: Optional[int]
    user_id: Optional[int]
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    date_of_death: Optional[date] = None
    gender: Optional[str] = None
    biography: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.first_name or not self.last_name:
            raise ValueError("Имя и фамилия обязательны")
        if self.date_of_death and self.date_of_birth:
            if self.date_of_death < self.date_of_birth:
                raise ValueError("Дата смерти не может быть раньше даты рождения")

    @property
    def full_name(self) -> str:
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return " ".join(parts)

    @property
    def age(self) -> Optional[int]:
        if not self.date_of_birth:
            return None
        end_date = self.date_of_death or date.today()
        return end_date.year - self.date_of_birth.year - (
            (end_date.month, end_date.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )

    @property
    def is_alive(self) -> bool:
        return self.date_of_death is None
```

### `core/domain/entities/relationship.py`

```python
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Optional


class RelationshipType(str, Enum):
    PARENT = "parent"
    CHILD = "child"
    SPOUSE = "spouse"
    SIBLING = "sibling"
    OTHER = "other"


@dataclass
class Relationship:
    """Доменная сущность связи между персонами"""
    id: Optional[int]
    person1_id: int
    person2_id: int
    relationship_type: RelationshipType
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if self.person1_id == self.person2_id:
            raise ValueError("Персона не может быть связана сама с собой")
        if self.end_date and self.start_date:
            if self.end_date < self.start_date:
                raise ValueError("Дата окончания не может быть раньше даты начала")

    def get_reverse_type(self) -> RelationshipType:
        """Возвращает обратный тип связи"""
        reverse_map = {
            RelationshipType.PARENT: RelationshipType.CHILD,
            RelationshipType.CHILD: RelationshipType.PARENT,
            RelationshipType.SPOUSE: RelationshipType.SPOUSE,
            RelationshipType.SIBLING: RelationshipType.SIBLING,
            RelationshipType.OTHER: RelationshipType.OTHER,
        }
        return reverse_map[self.relationship_type]
```

---

## Шаг 2: Интерфейсы репозиториев (Repository Interfaces)

### `core/domain/repositories/user_repository.py`

```python
from abc import ABC, abstractmethod
from typing import Optional, List
from core.domain.entities.user import User


class IUserRepository(ABC):
    """Интерфейс репозитория пользователей"""

    @abstractmethod
    def create(self, user: User) -> User:
        """Создать пользователя"""
        pass

    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Получить пользователя по email"""
        pass

    @abstractmethod
    def get_by_username(self, username: str) -> Optional[User]:
        """Получить пользователя по username"""
        pass

    @abstractmethod
    def update(self, user: User) -> User:
        """Обновить пользователя"""
        pass

    @abstractmethod
    def delete(self, user_id: int) -> bool:
        """Удалить пользователя"""
        pass

    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Получить список пользователей с пагинацией"""
        pass
```

### `core/domain/repositories/person_repository.py`

```python
from abc import ABC, abstractmethod
from typing import Optional, List
from core.domain.entities.person import Person


class IPersonRepository(ABC):
    """Интерфейс репозитория персон"""

    @abstractmethod
    def create(self, person: Person) -> Person:
        pass

    @abstractmethod
    def get_by_id(self, person_id: int) -> Optional[Person]:
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: int) -> Optional[Person]:
        pass

    @abstractmethod
    def update(self, person: Person) -> Person:
        pass

    @abstractmethod
    def delete(self, person_id: int) -> bool:
        pass

    @abstractmethod
    def search(self, query: str) -> List[Person]:
        """Поиск по имени/фамилии"""
        pass

    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Person]:
        pass
```

### `core/domain/repositories/relationship_repository.py`

```python
from abc import ABC, abstractmethod
from typing import Optional, List
from core.domain.entities.relationship import Relationship, RelationshipType


class IRelationshipRepository(ABC):
    """Интерфейс репозитория связей"""

    @abstractmethod
    def create(self, relationship: Relationship) -> Relationship:
        pass

    @abstractmethod
    def get_by_id(self, relationship_id: int) -> Optional[Relationship]:
        pass

    @abstractmethod
    def get_by_person_id(self, person_id: int) -> List[Relationship]:
        """Все связи персоны"""
        pass

    @abstractmethod
    def get_by_type(
        self, person_id: int, relationship_type: RelationshipType
    ) -> List[Relationship]:
        pass

    @abstractmethod
    def update(self, relationship: Relationship) -> Relationship:
        pass

    @abstractmethod
    def delete(self, relationship_id: int) -> bool:
        pass
```

---

## Шаг 3: DTO (Data Transfer Objects)

### `core/application/dto/user_dto.py`

```python
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional


class CreateUserDTO(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=8)


class UpdateUserDTO(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=2, max_length=50)
    is_active: Optional[bool] = None


class UserResponseDTO(BaseModel):
    id: int
    email: str
    username: str
    is_active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
```

### `core/application/dto/person_dto.py`

```python
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional


class CreatePersonDTO(BaseModel):
    user_id: Optional[int] = None
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[date] = None
    date_of_death: Optional[date] = None
    gender: Optional[str] = Field(None, pattern="^(male|female|other)$")
    biography: Optional[str] = None


class UpdatePersonDTO(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[date] = None
    date_of_death: Optional[date] = None
    gender: Optional[str] = None
    biography: Optional[str] = None


class PersonResponseDTO(BaseModel):
    id: int
    user_id: Optional[int]
    first_name: str
    last_name: str
    middle_name: Optional[str]
    full_name: str
    date_of_birth: Optional[date]
    date_of_death: Optional[date]
    age: Optional[int]
    is_alive: bool
    gender: Optional[str]
    biography: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
```

---

## Шаг 4: Use Cases

### `core/application/use_cases/user/create_user.py`

```python
from core.domain.entities.user import User
from core.domain.repositories.user_repository import IUserRepository
from core.application.dto.user_dto import CreateUserDTO
from core.infrastructure.auth.password_service import hash_password


class CreateUserUseCase:
    def __init__(self, user_repo: IUserRepository):
        self._user_repo = user_repo

    def execute(self, dto: CreateUserDTO) -> User:
        # Проверка уникальности email
        existing = self._user_repo.get_by_email(dto.email)
        if existing:
            raise ValueError(f"Email '{dto.email}' уже занят")

        # Проверка уникальности username
        existing = self._user_repo.get_by_username(dto.username)
        if existing:
            raise ValueError(f"Username '{dto.username}' уже занят")

        # Хеширование пароля
        password_hash = hash_password(dto.password)

        # Создание сущности
        user = User(
            id=None,
            email=dto.email,
            username=dto.username,
            password_hash=password_hash,
            is_active=True,
        )

        # Сохранение
        return self._user_repo.create(user)
```

### `core/application/use_cases/user/get_user.py`

```python
from typing import Optional
from core.domain.entities.user import User
from core.domain.repositories.user_repository import IUserRepository


class GetUserUseCase:
    def __init__(self, user_repo: IUserRepository):
        self._user_repo = user_repo

    def execute(self, user_id: int) -> Optional[User]:
        return self._user_repo.get_by_id(user_id)
```

### `core/application/use_cases/person/create_person.py`

```python
from core.domain.entities.person import Person
from core.domain.repositories.person_repository import IPersonRepository
from core.application.dto.person_dto import CreatePersonDTO


class CreatePersonUseCase:
    def __init__(self, person_repo: IPersonRepository):
        self._person_repo = person_repo

    def execute(self, dto: CreatePersonDTO) -> Person:
        person = Person(
            id=None,
            user_id=dto.user_id,
            first_name=dto.first_name,
            last_name=dto.last_name,
            middle_name=dto.middle_name,
            date_of_birth=dto.date_of_birth,
            date_of_death=dto.date_of_death,
            gender=dto.gender,
            biography=dto.biography,
        )
        return self._person_repo.create(person)
```

### `core/application/use_cases/person/get_person.py`

```python
from typing import Optional
from core.domain.entities.person import Person
from core.domain.repositories.person_repository import IPersonRepository


class GetPersonUseCase:
    def __init__(self, person_repo: IPersonRepository):
        self._person_repo = person_repo

    def execute(self, person_id: int) -> Optional[Person]:
        return self._person_repo.get_by_id(person_id)
```

---

## Шаг 5: SQLAlchemy модели (общие для SQLite и PostgreSQL)

> **Важно:** SQLAlchemy работает и с SQLite, и с PostgreSQL. Разница только в URL подключения.

### `core/infrastructure/database/models/base.py`

```python
from datetime import datetime
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Базовый класс для всех моделей"""
    pass


class TimestampMixin:
    """Миксин для автоматических created_at/updated_at"""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### `core/infrastructure/database/models/user_model.py`

```python
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

### `core/infrastructure/database/models/person_model.py`

```python
from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from core.infrastructure.database.models.base import Base, TimestampMixin
from core.domain.entities.person import Person


class PersonModel(Base, TimestampMixin):
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    date_of_death = Column(Date, nullable=True)
    gender = Column(String(10), nullable=True)
    biography = Column(Text, nullable=True)

    def to_domain(self) -> Person:
        return Person(
            id=self.id,
            user_id=self.user_id,
            first_name=self.first_name,
            last_name=self.last_name,
            middle_name=self.middle_name,
            date_of_birth=self.date_of_birth,
            date_of_death=self.date_of_death,
            gender=self.gender,
            biography=self.biography,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    @classmethod
    def from_domain(cls, person: Person) -> "PersonModel":
        return cls(
            id=person.id,
            user_id=person.user_id,
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
```

### `core/infrastructure/database/models/relationship_model.py`

```python
from sqlalchemy import Column, Integer, String, Date, ForeignKey, DateTime
from core.infrastructure.database.models.base import Base, TimestampMixin
from core.domain.entities.relationship import Relationship, RelationshipType


class RelationshipModel(Base, TimestampMixin):
    __tablename__ = "relationships"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    person1_id = Column(Integer, ForeignKey("persons.id"), nullable=False)
    person2_id = Column(Integer, ForeignKey("persons.id"), nullable=False)
    relationship_type = Column(String(20), nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    def to_domain(self) -> Relationship:
        return Relationship(
            id=self.id,
            person1_id=self.person1_id,
            person2_id=self.person2_id,
            relationship_type=RelationshipType(self.relationship_type),
            start_date=self.start_date,
            end_date=self.end_date,
            created_at=self.created_at,
        )

    @classmethod
    def from_domain(cls, rel: Relationship) -> "RelationshipModel":
        return cls(
            id=rel.id,
            person1_id=rel.person1_id,
            person2_id=rel.person2_id,
            relationship_type=rel.relationship_type.value,
            start_date=rel.start_date,
            end_date=rel.end_date,
            created_at=rel.created_at,
        )
```

### `core/infrastructure/database/models/__init__.py`

```python
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

---

## Шаг 6: Конфигурация БД (SQLite vs PostgreSQL)

### `core/infrastructure/database/config.py`

```python
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

load_dotenv()


class DatabaseConfig:
    """Конфигурация базы данных"""

    DB_TYPE = os.getenv("DB_TYPE", "sqlite").lower()  # "sqlite" или "postgres"

    # SQLite
    SQLITE_DB_DIR = os.getenv("SQLITE_DB_DIR", "~/Documents")
    SQLITE_DB_NAME = os.getenv("SQLITE_DB_NAME", "family_tree.db")

    # PostgreSQL
    POSTGRES_USER = os.getenv("POSTGRES_USER", "family_tree_user")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "your_password")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "family_tree_db")

    @classmethod
    def get_sync_url(cls) -> str:
        """URL для синхронного подключения (Desktop)"""
        if cls.DB_TYPE == "sqlite":
            db_path = Path(cls.SQLITE_DB_DIR).expanduser() / cls.SQLITE_DB_NAME
            db_path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite:///{db_path}"
        else:
            return (
                f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}"
                f"@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"
            )

    @classmethod
    def get_async_url(cls) -> str:
        """URL для асинхронного подключения (Web/API)"""
        if cls.DB_TYPE == "sqlite":
            db_path = Path(cls.SQLITE_DB_DIR).expanduser() / cls.SQLITE_DB_NAME
            db_path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite+aiosqlite:///{db_path}"
        else:
            return (
                f"postgresql+asyncpg://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}"
                f"@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"
            )

    @classmethod
    def is_sqlite(cls) -> bool:
        return cls.DB_TYPE == "sqlite"


# Синхронный движок (Desktop)
sync_engine = create_engine(
    DatabaseConfig.get_sync_url(),
    echo=False,
    connect_args={"check_same_thread": False} if DatabaseConfig.is_sqlite() else {},
)

SyncSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=sync_engine
)

# Асинхронный движок (Web/API)
async_engine = create_async_engine(
    DatabaseConfig.get_async_url(),
    echo=False,
)

AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)


def get_sync_session() -> Session:
    """Получить синхронную сессию (для Desktop)"""
    session = SyncSessionLocal()
    try:
        yield session
    finally:
        session.close()


async def get_async_session() -> AsyncSession:
    """Получить асинхронную сессию (для API)"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def init_db():
    """Создать таблицы (только для SQLite при первом запуске Desktop)"""
    from core.infrastructure.database.models import Base
    Base.metadata.create_all(bind=sync_engine)
```

---

## Шаг 7: Реализации репозиториев

### PostgreSQL (для API)

`core/infrastructure/database/repositories/postgres_user_repository.py`

```python
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.domain.repositories.user_repository import IUserRepository
from core.domain.entities.user import User
from core.infrastructure.database.models.user_model import UserModel


class PostgresUserRepositoryImpl(IUserRepository):
    """PostgreSQL реализация репозитория пользователей"""

    def __init__(self, db: AsyncSession):
        self._db = db

    async def create(self, user: User) -> User:
        db_model = UserModel.from_domain(user)
        self._db.add(db_model)
        await self._db.commit()
        await self._db.refresh(db_model)
        return db_model.to_domain()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self._db.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        db_model = result.scalar_one_or_none()
        return db_model.to_domain() if db_model else None

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self._db.execute(
            select(UserModel).where(UserModel.email == email)
        )
        db_model = result.scalar_one_or_none()
        return db_model.to_domain() if db_model else None

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self._db.execute(
            select(UserModel).where(UserModel.username == username)
        )
        db_model = result.scalar_one_or_none()
        return db_model.to_domain() if db_model else None

    async def update(self, user: User) -> User:
        db_model = await self.get_by_id(user.id)
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
        result = await self._db.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        db_model = result.scalar_one_or_none()
        if db_model:
            await self._db.delete(db_model)
            await self._db.commit()
            return True
        return False

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        result = await self._db.execute(
            select(UserModel).offset(skip).limit(limit)
        )
        db_models = result.scalars().all()
        return [model.to_domain() for model in db_models]
```

### SQLite (для Desktop)

`core/infrastructure/database/repositories/sqlite_user_repository.py`

```python
from typing import Optional, List
from sqlalchemy.orm import Session
from core.domain.repositories.user_repository import IUserRepository
from core.domain.entities.user import User
from core.infrastructure.database.models.user_model import UserModel


class SQLiteUserRepositoryImpl(IUserRepository):
    """SQLite реализация репозитория пользователей"""

    def __init__(self, db: Session):
        self._db = db

    def create(self, user: User) -> User:
        db_model = UserModel.from_domain(user)
        self._db.add(db_model)
        self._db.commit()
        self._db.refresh(db_model)
        return db_model.to_domain()

    def get_by_id(self, user_id: int) -> Optional[User]:
        db_model = (
            self._db.query(UserModel).filter(UserModel.id == user_id).first()
        )
        return db_model.to_domain() if db_model else None

    def get_by_email(self, email: str) -> Optional[User]:
        db_model = (
            self._db.query(UserModel).filter(UserModel.email == email).first()
        )
        return db_model.to_domain() if db_model else None

    def get_by_username(self, username: str) -> Optional[User]:
        db_model = (
            self._db.query(UserModel).filter(UserModel.username == username).first()
        )
        return db_model.to_domain() if db_model else None

    def update(self, user: User) -> User:
        db_model = self.get_by_id(user.id)
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
        db_model = (
            self._db.query(UserModel).filter(UserModel.id == user_id).first()
        )
        if db_model:
            self._db.delete(db_model)
            self._db.commit()
            return True
        return False

    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        db_models = self._db.query(UserModel).offset(skip).limit(limit).all()
        return [model.to_domain() for model in db_models]
```

---

## Шаг 8: Фабрика репозиториев

### `core/infrastructure/database/repository_factory.py`

```python
from typing import Union
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.repositories.user_repository import IUserRepository
from core.domain.repositories.person_repository import IPersonRepository

from core.infrastructure.database.repositories.sqlite_user_repository import SQLiteUserRepositoryImpl
from core.infrastructure.database.repositories.postgres_user_repository import PostgresUserRepositoryImpl
from core.infrastructure.database.config import DatabaseConfig


def create_user_repository(
    db_session: Union[Session, AsyncSession]
) -> IUserRepository:
    """
    Фабрика репозитория пользователей.
    Автоматически выбирает реализацию на основе типа сессии.
    """
    if isinstance(db_session, AsyncSession):
        return PostgresUserRepositoryImpl(db_session)
    else:
        return SQLiteUserRepositoryImpl(db_session)


def create_person_repository(
    db_session: Union[Session, AsyncSession]
) -> IPersonRepository:
    """
    Фабрика репозитория персон.
    """
    # Аналогично: если AsyncSession → Postgres, иначе → SQLite
    # (реализацию напиши сам по аналогии с User)
    pass
```

---

## Шаг 9: Аутентификация

### `core/infrastructure/auth/password_service.py`

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Хешировать пароль"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверить пароль"""
    return pwd_context.verify(plain_password, hashed_password)
```

### `core/infrastructure/auth/jwt_service.py`

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_DAYS = int(os.getenv("ACCESS_TOKEN_EXPIRE_DAYS", 1))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создать JWT токен"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Расшифровать JWT токен"""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
```

---

## Шаг 10: Использование в API (FastAPI)

### `api/dependencies/database.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession
from core.infrastructure.database.config import get_async_session


async def get_db() -> AsyncSession:
    """FastAPI зависимость для получения сессии БД"""
    async for session in get_async_session():
        yield session
```

### `api/routes/users.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.application.dto.user_dto import CreateUserDTO, UserResponseDTO
from core.application.use_cases.user.create_user import CreateUserUseCase
from core.infrastructure.database.repositories.postgres_user_repository import PostgresUserRepositoryImpl
from api.dependencies.database import get_db

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/", response_model=UserResponseDTO, status_code=status.HTTP_201_CREATED)
async def create_user(dto: CreateUserDTO, db: AsyncSession = Depends(get_db)):
    """Создать пользователя"""
    try:
        repo = PostgresUserRepositoryImpl(db)
        use_case = CreateUserUseCase(repo)
        user = await use_case.execute(dto)
        return UserResponseDTO.model_validate(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}", response_model=UserResponseDTO)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """Получить пользователя по ID"""
    from core.application.use_cases.user.get_user import GetUserUseCase

    repo = PostgresUserRepositoryImpl(db)
    use_case = GetUserUseCase(repo)
    user = await use_case.execute(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponseDTO.model_validate(user)
```

### `api/main.py`

```python
from fastapi import FastAPI
from api.routes import users

app = FastAPI(title="Family Tree API", version="0.1.0")

app.include_router(users.router)


@app.get("/")
def root():
    return {"message": "Family Tree API", "version": "0.1.0"}
```

---

## Шаг 11: Использование в Desktop

### `desktop/main.py`

```python
from sqlalchemy.orm import Session
from core.infrastructure.database.config import init_db, get_sync_session
from core.infrastructure.database.repositories.sqlite_user_repository import SQLiteUserRepositoryImpl
from core.application.use_cases.user.create_user import CreateUserUseCase
from core.application.dto.user_dto import CreateUserDTO


def main():
    # Инициализация БД (создать таблицы)
    init_db()

    # Получить сессию
    with next(get_sync_session()) as db:
        # Создать репозиторий
        repo = SQLiteUserRepositoryImpl(db)

        # Создать Use Case
        create_use_case = CreateUserUseCase(repo)

        # Создать пользователя
        dto = CreateUserDTO(
            email="test@example.com",
            username="testuser",
            password="securepassword123",
        )

        try:
            user = create_use_case.execute(dto)
            print(f"Создан пользователь: {user.username} (id={user.id})")
        except ValueError as e:
            print(f"Ошибка: {e}")


if __name__ == "__main__":
    main()
```

---

## Шаг 12: Конфигурация (.env)

### Для Desktop (SQLite)

```env
DB_TYPE=sqlite
SQLITE_DB_DIR=~/Documents
SQLITE_DB_NAME=family_tree.db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_DAYS=1
```

### Для Web (PostgreSQL)

```env
DB_TYPE=postgres
POSTGRES_USER=family_tree_user
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=family_tree_db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_DAYS=1
```

---

## Шаг 13: Синхронизация данных

### `tools/sync_databases.py`

```python
"""
Скрипт для синхронизации данных между SQLite и PostgreSQL.

Использование:
    # Экспорт из PostgreSQL в SQLite
    python -m tools.sync_databases --from postgres --to sqlite

    # Импорт из SQLite в PostgreSQL
    python -m tools.sync_databases --from sqlite --to postgres
"""

import argparse
import json
from datetime import date, datetime
from sqlalchemy import create_engine, text
from pathlib import Path


class DatabaseSync:
    """Синхронизация между SQLite и PostgreSQL"""

    def __init__(self, source_url: str, target_url: str):
        self.source_engine = create_engine(source_url)
        self.target_engine = create_engine(target_url)

    def export_table(self, table_name: str) -> list[dict]:
        """Экспорт таблицы в список словарей"""
        with self.source_engine.connect() as conn:
            result = conn.execute(text(f"SELECT * FROM {table_name}"))
            columns = result.keys()
            rows = []
            for row in result:
                row_dict = dict(zip(columns, row))
                # Конвертация дат в строки для JSON
                for key, value in row_dict.items():
                    if isinstance(value, (date, datetime)):
                        row_dict[key] = value.isoformat()
                rows.append(row_dict)
            return rows

    def import_table(self, table_name: str, data: list[dict]):
        """Импорт данных в таблицу"""
        if not data:
            return

        with self.target_engine.connect() as conn:
            # Получить колонки
            columns = data[0].keys()
            columns_str = ", ".join(columns)
            placeholders = ", ".join([f":{col}" for col in columns])

            # Вставить данные (игнорировать дубликаты по ID)
            insert_sql = f"""
                INSERT INTO {table_name} ({columns_str})
                VALUES ({placeholders})
                ON CONFLICT (id) DO NOTHING
            """

            conn.execute(text(insert_sql), data)
            conn.commit()

    def sync_table(self, table_name: str):
        """Синхронизировать таблицу"""
        print(f"Синхронизация таблицы '{table_name}'...")
        data = self.export_table(table_name)
        print(f"  Экспортировано {len(data)} записей")
        self.import_table(table_name, data)
        print(f"  Импортировано {len(data)} записей")


def get_db_url(db_type: str) -> str:
    """Получить URL базы данных"""
    if db_type == "sqlite":
        db_path = Path("~/Documents/family_tree.db").expanduser()
        return f"sqlite:///{db_path}"
    else:
        return "postgresql://family_tree_user:your_password@localhost:5432/family_tree_db"


def main():
    parser = argparse.ArgumentParser(description="Синхронизация БД")
    parser.add_argument("--from", dest="source", choices=["sqlite", "postgres"], required=True)
    parser.add_argument("--to", dest="target", choices=["sqlite", "postgres"], required=True)
    args = parser.parse_args()

    source_url = get_db_url(args.source)
    target_url = get_db_url(args.target)

    sync = DatabaseSync(source_url, target_url)

    # Синхронизировать все таблицы
    tables = ["users", "persons", "relationships"]
    for table in tables:
        try:
            sync.sync_table(table)
        except Exception as e:
            print(f"  Ошибка синхронизации '{table}': {e}")

    print("Синхронизация завершена!")


if __name__ == "__main__":
    main()
```

---

## Шаг 14: Alembic миграции

### `alembic.ini`

```ini
[alembic]
script_location = alembic
sqlalchemy.url = postgresql://family_tree_user:your_password@localhost:5432/family_tree_db
```

### `alembic/env.py`

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from core.infrastructure.database.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### Создание миграции

```bash
# Инициализация Alembic
alembic init alembic

# Создание миграции
alembic revision --autogenerate -m "initial tables"

# Применение миграции
alembic upgrade head
```

---

## Шаг 15: requirements

### `requirements/base.txt` (общие)

```
SQLAlchemy==2.0.37
Pydantic==2.10.5
pydantic-settings==2.7.1
python-dotenv==1.0.1
passlib==1.7.4
bcrypt==4.0.1
python-jose==3.5.0
alembic==1.14.0
```

### `requirements/api.txt` (для Web)

```
-r base.txt
fastapi==0.115.6
uvicorn==0.34.0
asyncpg==0.30.0
python-multipart==0.0.20
```

### `requirements/desktop.txt` (для Desktop)

```
-r base.txt
PyQt6==6.7.0
# или
# PySide6==6.7.0
```

### `requirements/dev.txt`

```
-r api.txt
-r desktop.txt
pytest==8.3.4
pytest-asyncio==0.23.3
```

---

## Чек-лист реализации

- [ ] Создать доменные сущности (`User`, `Person`, `Relationship`)
- [ ] Создать интерфейсы репозиториев (`IUserRepository`, `IPersonRepository`, `IRelationshipRepository`)
- [ ] Создать DTO (`CreateUserDTO`, `UserResponseDTO`, `CreatePersonDTO`, `PersonResponseDTO`)
- [ ] Создать Use Cases (`CreateUserUseCase`, `GetUserUseCase`, `CreatePersonUseCase`, `GetPersonUseCase`)
- [ ] Создать SQLAlchemy модели (`UserModel`, `PersonModel`, `RelationshipModel`)
- [ ] Настроить конфигурацию БД (`DatabaseConfig` с SQLite и PostgreSQL)
- [ ] Реализовать PostgreSQL репозитории (async)
- [ ] Реализовать SQLite репозитории (sync)
- [ ] Создать фабрику репозиториев
- [ ] Настроить аутентификацию (`password_service`, `jwt_service`)
- [ ] Создать API роуты
- [ ] Создать Desktop приложение
- [ ] Написать скрипт синхронизации
- [ ] Настроить Alembic миграции

---

## Запуск

### API (PostgreSQL)

```bash
# Установить зависимости
pip install -r requirements/api.txt

# Создать .env с DB_TYPE=postgres

# Применить миграции
alembic upgrade head

# Запустить API
uvicorn api.main:app --reload
```

### Desktop (SQLite)

```bash
# Установить зависимости
pip install -r requirements/desktop.txt

# Создать .env с DB_TYPE=sqlite

# Запустить
python -m desktop.main
```

### Синхронизация

```bash
# Из SQLite в PostgreSQL
python -m tools.sync_databases --from sqlite --to postgres

# Из PostgreSQL в SQLite
python -m tools.sync_databases --from postgres --to sqlite
```
