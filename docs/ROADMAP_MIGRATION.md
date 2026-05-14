# Дорожная карта: Миграция от простого Tkinter к Clean Architecture

## Введение

Этот документ описывает пошаговый план перехода от простого однофайлового приложения на Tkinter (см. `genealogy_app_plan.md`) к полноценной архитектуре с разделением на слои (см. `docs/ARCHITECTURE.md`).

### Исходное состояние

```
genealogy_app/
├── main.py
├── database.py          # SQLAlchemy engine, SessionLocal
├── models.py            # Person, Relationship через declarative_base()
└── gui.py               # Весь UI в одном файле
```

### Целевое состояние

```
family_tree/
├── core/
│   ├── domain/          # Entities, Repository Interfaces
│   ├── application/     # Use Cases, DTO, Interfaces
│   └── infrastructure/  # DB Models, Repository Implementations, Auth
├── api/                 # FastAPI
├── desktop/             # PyQt/Tkinter
└── tests/
```

---

## Этап 0: Подготовка (1-2 дня)

### Задачи

1. **Изучить концепцию Clean Architecture**
   - Прочитать документацию: `docs/ARCHITECTURE.md`, `docs/PROJECT_STRUCTURE.md`
   - Понять принцип Dependency Inversion (domain не зависит от infrastructure)
   - Нарисовать схему слоёв на бумаге

2. **Оценить текущий код**
   - Прочитать `genealogy_app_plan.md`
   - Выписать все сущности (Person, Relationship)
   - Выписать все операции (CRUD, управление связями)

3. **Создать новую структуру папок**
```bash
mkdir -p family_tree/{core/{domain/{entities,repositories,services},application/{use_cases/{person,relationship,user},dto,interfaces},infrastructure/{database/{models,repositories},auth,config}},api/{routes,dependencies,middleware},desktop/{ui,views,controllers},shared,tests/{unit,integration,e2e,fixtures},alembic/versions,requirements}
touch family_tree/{core,core/domain,core/application,core/infrastructure,api,desktop,shared,tests}/__init__.py
```

4. **Создать базовые конфигурационные файлы**
   - `pyproject.toml` — управление зависимостями
   - `requirements/base.txt` — SQLAlchemy, Pydantic
   - `requirements/api.txt` — FastAPI, uvicorn
   - `requirements/desktop.txt` — PyQt6 или Tkinter
   - `requirements/dev.txt` — pytest, mypy, black
   - `.env.example` — пример конфигурации
   - `.gitignore`

---

## Этап 1: Доменный слой (Domain Layer) — 2-3 дня

### Цель
Создать независимые от технологий бизнес-сущности и интерфейсы.

### Задачи

#### 1.1 Entity Person (0.5 дня)

**Файл:** `core/domain/entities/person.py`

```python
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class Gender(Enum):
    MALE = "M"
    FEMALE = "F"
    OTHER = "O"


@dataclass
class Person:
    """Доменная сущность Person"""
    id: Optional[int] = None
    first_name: str = ""
    last_name: str = ""
    birth_date: Optional[date] = None
    death_date: Optional[date] = None
    gender: Optional[Gender] = None
    notes: Optional[str] = None
    owner_id: Optional[int] = None  # Для мультипользовательской версии
    
    def __post_init__(self):
        if self.gender and isinstance(self.gender, str):
            self.gender = Gender(self.gender)
```

**Что учтено:**
- Использует `dataclass` для простоты
- `Optional[int]` для id (ещё нет в БД)
- `Gender` как Enum (валидация)
- Никаких импортов из SQLAlchemy

#### 1.2 Entity Relationship (0.5 дня)

**Файл:** `core/domain/entities/relationship.py`

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class RelationshipType(Enum):
    FATHER = "father"
    MOTHER = "mother"
    SPOUSE = "spouse"
    CHILD = "child"
    SIBLING = "sibling"
    
    def get_reverse(self) -> "RelationshipType":
        """Возвращает обратный тип связи"""
        mapping = {
            "father": "child",
            "mother": "child",
            "child": "father",  # или "mother" — зависит от контекста
            "spouse": "spouse",
            "sibling": "sibling"
        }
        return RelationshipType(mapping[self.value])


@dataclass
class Relationship:
    """Связь между двумя людьми"""
    id: Optional[int] = None
    person_id: int = 0
    related_person_id: int = 0
    relationship_type: Optional[RelationshipType] = None
    owner_id: Optional[int] = None
    
    def __post_init__(self):
        if self.relationship_type and isinstance(self.relationship_type, str):
            self.relationship_type = RelationshipType(self.relationship_type)
```

#### 1.3 Интерфейсы репозиториев (1 день)

**Файл:** `core/domain/repositories/person_repository.py`

```python
from abc import ABC, abstractmethod
from typing import Optional, List
from core.domain.entities.person import Person


class IPersonRepository(ABC):
    """Интерфейс репозитория Person"""
    
    @abstractmethod
    def create(self, person: Person) -> Person:
        """Создать персону"""
        pass
    
    @abstractmethod
    def get_by_id(self, person_id: int) -> Optional[Person]:
        """Получить по ID"""
        pass
    
    @abstractmethod
    def get_all(self, owner_id: int) -> List[Person]:
        """Получить всех персон владельца"""
        pass
    
    @abstractmethod
    def update(self, person: Person) -> Person:
        """Обновить персону"""
        pass
    
    @abstractmethod
    def delete(self, person_id: int) -> None:
        """Удалить персону"""
        pass
    
    @abstractmethod
    def search(self, query: str, owner_id: int) -> List[Person]:
        """Поиск по имени/фамилии"""
        pass
```

**Файл:** `core/domain/repositories/relationship_repository.py`

```python
from abc import ABC, abstractmethod
from typing import Optional, List
from core.domain.entities.relationship import Relationship


class IRelationshipRepository(ABC):
    """Интерфейс репозитория Relationship"""
    
    @abstractmethod
    def create(self, relationship: Relationship) -> Relationship:
        pass
    
    @abstractmethod
    def get_by_id(self, relationship_id: int) -> Optional[Relationship]:
        pass
    
    @abstractmethod
    def get_by_person_id(self, person_id: int) -> List[Relationship]:
        pass
    
    @abstractmethod
    def delete(self, relationship_id: int) -> None:
        pass
```

### Итоги этапа 1

✅ Domain-модели не зависят от SQLAlchemy  
✅ Интерфейсы определены  
✅ Можно писать unit-тесты без БД  

---

## Этап 2: Application слой (Use Cases + DTO) — 3-4 дня

### Цель
Создать бизнес-операции (use cases) и DTO для передачи данных.

### Задачи

#### 2.1 DTO (1 день)

**Файл:** `core/application/dto/person_dto.py`

```python
from dataclasses import dataclass
from datetime import date
from typing import Optional
from core.domain.entities.person import Gender


@dataclass
class CreatePersonDTO:
    first_name: str
    last_name: str
    birth_date: Optional[date] = None
    death_date: Optional[date] = None
    gender: Optional[Gender] = None
    notes: Optional[str] = None
    owner_id: Optional[int] = None


@dataclass
class UpdatePersonDTO:
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_date: Optional[date] = None
    death_date: Optional[date] = None
    gender: Optional[Gender] = None
    notes: Optional[str] = None
```

**Файл:** `core/application/dto/relationship_dto.py`

```python
from dataclasses import dataclass
from typing import Optional
from core.domain.entities.relationship import RelationshipType


@dataclass
class CreateRelationshipDTO:
    person_id: int
    related_person_id: int
    relationship_type: RelationshipType
```

#### 2.2 Use Cases (2-3 дня)

**Файл:** `core/application/use_cases/person/create_person.py`

```python
from core.domain.entities.person import Person
from core.domain.repositories.person_repository import IPersonRepository
from core.application.dto.person_dto import CreatePersonDTO


class CreatePersonUseCase:
    def __init__(self, person_repo: IPersonRepository):
        self._person_repo = person_repo
    
    def execute(self, dto: CreatePersonDTO) -> Person:
        """Создать новую персону"""
        person = Person(
            first_name=dto.first_name,
            last_name=dto.last_name,
            birth_date=dto.birth_date,
            death_date=dto.death_date,
            gender=dto.gender,
            notes=dto.notes,
            owner_id=dto.owner_id
        )
        return self._person_repo.create(person)
```

**Файл:** `core/application/use_cases/person/get_person.py`

```python
from typing import Optional
from core.domain.entities.person import Person
from core.domain.repositories.person_repository import IPersonRepository


class GetPersonUseCase:
    def __init__(self, person_repo: IPersonRepository):
        self._person_repo = person_repo
    
    def execute(self, person_id: int, owner_id: int) -> Optional[Person]:
        """Получить персону по ID"""
        person = self._person_repo.get_by_id(person_id)
        if person and person.owner_id != owner_id:
            return None  # Не принадлежит пользователю
        return person
```

**Файл:** `core/application/use_cases/person/update_person.py`

```python
from typing import Optional
from core.domain.entities.person import Person
from core.domain.repositories.person_repository import IPersonRepository
from core.application.dto.person_dto import UpdatePersonDTO


class UpdatePersonUseCase:
    def __init__(self, person_repo: IPersonRepository):
        self._person_repo = person_repo
    
    def execute(self, person_id: int, dto: UpdatePersonDTO, owner_id: int) -> Optional[Person]:
        """Обновить персону"""
        person = self._person_repo.get_by_id(person_id)
        
        if not person or person.owner_id != owner_id:
            return None
        
        # Обновляем только переданные поля
        if dto.first_name is not None:
            person.first_name = dto.first_name
        if dto.last_name is not None:
            person.last_name = dto.last_name
        if dto.birth_date is not None:
            person.birth_date = dto.birth_date
        if dto.death_date is not None:
            person.death_date = dto.death_date
        if dto.gender is not None:
            person.gender = dto.gender
        if dto.notes is not None:
            person.notes = dto.notes
        
        return self._person_repo.update(person)
```

**Файл:** `core/application/use_cases/person/delete_person.py`

```python
from typing import Optional
from core.domain.repositories.person_repository import IPersonRepository


class DeletePersonUseCase:
    def __init__(self, person_repo: IPersonRepository):
        self._person_repo = person_repo
    
    def execute(self, person_id: int, owner_id: int) -> bool:
        """Удалить персону (каскадно удаляются связи)"""
        person = self._person_repo.get_by_id(person_id)
        
        if not person or person.owner_id != owner_id:
            return False
        
        self._person_repo.delete(person_id)
        return True
```

**Файл:** `core/application/use_cases/person/get_all_persons.py`

```python
from typing import List
from core.domain.entities.person import Person
from core.domain.repositories.person_repository import IPersonRepository


class GetAllPersonsUseCase:
    def __init__(self, person_repo: IPersonRepository):
        self._person_repo = person_repo
    
    def execute(self, owner_id: int) -> List[Person]:
        """Получить всех персон владельца"""
        return self._person_repo.get_all(owner_id)
```

**Файл:** `core/application/use_cases/relationship/create_relationship.py`

```python
from core.domain.entities.relationship import Relationship
from core.domain.repositories.relationship_repository import IRelationshipRepository
from core.domain.repositories.person_repository import IPersonRepository
from core.application.dto.relationship_dto import CreateRelationshipDTO


class CreateRelationshipUseCase:
    def __init__(
        self, 
        relationship_repo: IRelationshipRepository,
        person_repo: IPersonRepository
    ):
        self._relationship_repo = relationship_repo
        self._person_repo = person_repo
    
    def execute(self, dto: CreateRelationshipDTO, owner_id: int) -> Relationship:
        """Создать связь между людьми"""
        # Проверить что обе персоны существуют и принадлежат пользователю
        person1 = self._person_repo.get_by_id(dto.person_id)
        person2 = self._person_repo.get_by_id(dto.related_person_id)
        
        if not person1 or not person2:
            raise ValueError("Одна из персон не найдена")
        
        if person1.owner_id != owner_id or person2.owner_id != owner_id:
            raise ValueError("Персоны не принадлежат пользователю")
        
        relationship = Relationship(
            person_id=dto.person_id,
            related_person_id=dto.related_person_id,
            relationship_type=dto.relationship_type,
            owner_id=owner_id
        )
        
        return self._relationship_repo.create(relationship)
```

**Файл:** `core/application/use_cases/relationship/get_relationships.py`

```python
from typing import List
from core.domain.entities.relationship import Relationship
from core.domain.repositories.relationship_repository import IRelationshipRepository


class GetRelationshipsUseCase:
    def __init__(self, relationship_repo: IRelationshipRepository):
        self._relationship_repo = relationship_repo
    
    def execute(self, person_id: int) -> List[Relationship]:
        """Получить все связи персоны"""
        return self._relationship_repo.get_by_person_id(person_id)
```

**Файл:** `core/application/use_cases/relationship/delete_relationship.py`

```python
from core.domain.repositories.relationship_repository import IRelationshipRepository


class DeleteRelationshipUseCase:
    def __init__(self, relationship_repo: IRelationshipRepository):
        self._relationship_repo = relationship_repo
    
    def execute(self, relationship_id: int) -> bool:
        """Удалить связь"""
        rel = self._relationship_repo.get_by_id(relationship_id)
        if not rel:
            return False
        
        self._relationship_repo.delete(relationship_id)
        return True
```

### Итоги этапа 2

✅ Use Cases зависят только от интерфейсов репозиториев  
✅ DTO для передачи данных  
✅ Бизнес-логика изолирована от UI и БД  

---

## Этап 3: Infrastructure слой (SQLAlchemy модели + реализации) — 3-4 дня

### Цель
Реализовать репозитории с использованием SQLAlchemy и создать модели БД.

### Задачи

#### 3.1 SQLAlchemy Base и конфигурация (0.5 дня)

**Файл:** `core/infrastructure/database/models/base.py`

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Базовый класс для SQLAlchemy моделей (SQLAlchemy 2.0)"""
    pass
```

**Файл:** `core/infrastructure/database/config.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.infrastructure.config.settings import settings

engine = create_engine(
    settings.database_url,
    echo=settings.db_echo,
    future=True
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False
)


def get_db():
    """Context manager для сессии БД"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
```

**Файл:** `core/infrastructure/config/settings.py`

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    database_url: str = "sqlite:///./genealogy.db"
    db_echo: bool = False


settings = Settings()
```

#### 3.2 SQLAlchemy модели (1 день)

**Файл:** `core/infrastructure/database/models/person_model.py`

```python
from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.infrastructure.database.models.base import Base


class PersonModel(Base):
    __tablename__ = "person"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    birth_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    death_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    gender: Mapped[str] = mapped_column(String(1), default="M")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_id: Mapped[int | None] = mapped_column(nullable=True)
    
    # Отношения
    relationships_as_person: Mapped[list[RelationshipModel]] = relationship(
        back_populates="person",
        foreign_keys="[RelationshipModel.person_id]",
        cascade="all, delete-orphan"
    )
    
    def to_domain(self) -> "Person":
        """Преобразовать в доменную сущность"""
        from core.domain.entities.person import Gender, Person
        
        return Person(
            id=self.id,
            first_name=self.first_name,
            last_name=self.last_name,
            birth_date=self.birth_date,
            death_date=self.death_date,
            gender=Gender(self.gender) if self.gender else None,
            notes=self.notes,
            owner_id=self.owner_id
        )
    
    @classmethod
    def from_domain(cls, person: "Person") -> "PersonModel":
        """Создать из доменной сущности"""
        return cls(
            id=person.id,
            first_name=person.first_name,
            last_name=person.last_name,
            birth_date=person.birth_date,
            death_date=person.death_date,
            gender=person.gender.value if person.gender else "M",
            notes=person.notes,
            owner_id=person.owner_id
        )
```

**Файл:** `core/infrastructure/database/models/relationship_model.py`

```python
from __future__ import annotations

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.infrastructure.database.models.base import Base


class RelationshipModel(Base):
    __tablename__ = "relationship"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("person.id"), nullable=False)
    related_person_id: Mapped[int] = mapped_column(ForeignKey("person.id"), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False)
    
    person: Mapped[PersonModel] = relationship(
        back_populates="relationships_as_person",
        foreign_keys=[person_id]
    )
    
    def to_domain(self) -> "Relationship":
        from core.domain.entities.relationship import Relationship, RelationshipType
        return Relationship(
            id=self.id,
            person_id=self.person_id,
            related_person_id=self.related_person_id,
            relationship_type=RelationshipType(self.relationship_type)
        )
    
    @classmethod
    def from_domain(cls, rel: "Relationship") -> "RelationshipModel":
        return cls(
            id=rel.id,
            person_id=rel.person_id,
            related_person_id=rel.related_person_id,
            relationship_type=rel.relationship_type.value if rel.relationship_type else ""
        )
```

#### 3.3 Реализации репозиториев (2 дня)

**Файл:** `core/infrastructure/database/repositories/sqlalchemy_person_repository.py`

```python
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import Session
from core.domain.entities.person import Person, Gender
from core.domain.repositories.person_repository import IPersonRepository
from core.infrastructure.database.models.person_model import PersonModel


class SQLAlchemyPersonRepository(IPersonRepository):
    def __init__(self, db_session: Session):
        self.session = db_session
    
    def create(self, person: Person) -> Person:
        model = PersonModel.from_domain(person)
        self.session.add(model)
        self.session.flush()  # Получить ID
        person.id = model.id
        return person
    
    def get_by_id(self, person_id: int) -> Optional[Person]:
        stmt = select(PersonModel).where(PersonModel.id == person_id)
        model = self.session.execute(stmt).scalar_one_or_none()
        return model.to_domain() if model else None
    
    def get_all(self, owner_id: int) -> List[Person]:
        stmt = select(PersonModel).where(PersonModel.owner_id == owner_id)
        models = self.session.execute(stmt).scalars().all()
        return [m.to_domain() for m in models]
    
    def update(self, person: Person) -> Person:
        stmt = select(PersonModel).where(PersonModel.id == person.id)
        model = self.session.execute(stmt).scalar_one_or_none()
        if model:
            model.first_name = person.first_name
            model.last_name = person.last_name
            model.birth_date = person.birth_date
            model.death_date = person.death_date
            model.gender = person.gender.value if person.gender else "M"
            model.notes = person.notes
        return person
    
    def delete(self, person_id: int) -> None:
        stmt = select(PersonModel).where(PersonModel.id == person_id)
        model = self.session.execute(stmt).scalar_one_or_none()
        if model:
            self.session.delete(model)
    
    def search(self, query: str, owner_id: int) -> List[Person]:
        search_pattern = f"%{query}%"
        stmt = select(PersonModel).where(
            (PersonModel.owner_id == owner_id) &
            ((PersonModel.first_name.like(search_pattern)) | 
             (PersonModel.last_name.like(search_pattern)))
        )
        models = self.session.execute(stmt).scalars().all()
        return [m.to_domain() for m in models]
```

**Файл:** `core/infrastructure/database/repositories/sqlalchemy_relationship_repository.py`

```python
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import Session
from core.domain.entities.relationship import Relationship, RelationshipType
from core.domain.repositories.relationship_repository import IRelationshipRepository
from core.infrastructure.database.models.relationship_model import RelationshipModel


class SQLAlchemyRelationshipRepository(IRelationshipRepository):
    def __init__(self, db_session: Session):
        self.session = db_session
    
    def create(self, relationship: Relationship) -> Relationship:
        model = RelationshipModel.from_domain(relationship)
        self.session.add(model)
        self.session.flush()
        relationship.id = model.id
        return relationship
    
    def get_by_id(self, relationship_id: int) -> Optional[Relationship]:
        stmt = select(RelationshipModel).where(RelationshipModel.id == relationship_id)
        model = self.session.execute(stmt).scalar_one_or_none()
        return model.to_domain() if model else None
    
    def get_by_person_id(self, person_id: int) -> List[Relationship]:
        stmt = select(RelationshipModel).where(RelationshipModel.person_id == person_id)
        models = self.session.execute(stmt).scalars().all()
        return [m.to_domain() for m in models]
    
    def delete(self, relationship_id: int) -> None:
        stmt = select(RelationshipModel).where(RelationshipModel.id == relationship_id)
        model = self.session.execute(stmt).scalar_one_or_none()
        if model:
            self.session.delete(model)
```

### Итоги этапа 3

✅ SQLAlchemy модели с `to_domain()`/`from_domain()`  
✅ Реализации репозиториев  
✅ Инфраструктура отделена от домена  

---

## Этап 4: Desktop-клиент с использованием Use Cases — 3-4 дня

### Цель
Заменить старый монолитный `gui.py` на архитектуру MVC с использованием Use Cases.

### Задачи

#### 4.1 Dependency Injection (0.5 дня)

**Файл:** `desktop/app.py`

```python
from sqlalchemy.orm import Session
from core.domain.repositories.person_repository import IPersonRepository
from core.domain.repositories.relationship_repository import IRelationshipRepository
from core.application.use_cases.person.create_person import CreatePersonUseCase
from core.application.use_cases.person.get_person import GetPersonUseCase
from core.infrastructure.database.repositories.sqlalchemy_person_repository import SQLAlchemyPersonRepository
from core.infrastructure.database.repositories.sqlalchemy_relationship_repository import SQLAlchemyRelationshipRepository


class AppContainer:
    """DI-контейнер для Desktop приложения"""
    
    def __init__(self, db_session: Session):
        self._session = db_session
        
        # Repositories
        self._person_repo = SQLAlchemyPersonRepository(db_session)
        self._relationship_repo = SQLAlchemyRelationshipRepository(db_session)
        
        # Use Cases
        self.create_person = CreatePersonUseCase(self._person_repo)
        self.get_person = GetPersonUseCase(self._person_repo)
    
    @property
    def person_repo(self) -> IPersonRepository:
        return self._person_repo
    
    @property
    def relationship_repo(self) -> IRelationshipRepository:
        return self._relationship_repo
```

#### 4.2 Контроллеры (1 день)

**Файл:** `desktop/controllers/person_controller.py`

```python
from typing import Optional
from core.application.use_cases.person.create_person import CreatePersonUseCase
from core.application.use_cases.person.get_person import GetPersonUseCase
from core.application.use_cases.person.update_person import UpdatePersonUseCase
from core.application.use_cases.person.delete_person import DeletePersonUseCase
from core.application.dto.person_dto import CreatePersonDTO, UpdatePersonDTO
from core.domain.entities.person import Person


class PersonController:
    def __init__(
        self,
        create_person: CreatePersonUseCase,
        get_person: GetPersonUseCase,
        update_person: UpdatePersonUseCase,
        delete_person: DeletePersonUseCase
    ):
        self._create_person = create_person
        self._get_person = get_person
        self._update_person = update_person
        self._delete_person = delete_person
    
    def create_person(self, first_name: str, last_name: str, **kwargs) -> Person:
        dto = CreatePersonDTO(first_name=first_name, last_name=last_name, **kwargs)
        return self._create_person.execute(dto)
    
    def get_person(self, person_id: int) -> Optional[Person]:
        return self._get_person.execute(person_id)
    
    def update_person(self, person: Person) -> Person:
        return self._update_person.execute(person)
    
    def delete_person(self, person_id: int) -> None:
        self._delete_person.execute(person_id)
```

#### 4.3 Views (1.5 дня)

**Файл:** `desktop/views/main_view.py`

```python
import tkinter as tk
from tkinter import ttk
from typing import List
from core.domain.entities.person import Person
from desktop.controllers.person_controller import PersonController


class MainView(tk.Tk):
    def __init__(self, controller: PersonController):
        super().__init__()
        self.controller = controller
        self.title("Genealogy App")
        self.geometry("800x600")
        
        self._create_widgets()
        self._load_people()
    
    def _create_widgets(self):
        # Toolbar
        toolbar = ttk.Frame(self, padding=10)
        toolbar.pack(fill=tk.X)
        
        ttk.Button(toolbar, text="Добавить", command=self._on_add).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Редактировать", command=self._on_edit).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Удалить", command=self._on_delete).pack(side=tk.LEFT)
        
        # Table
        table_frame = ttk.Frame(self, padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("ID", "Имя", "Фамилия", "Дата рождения")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
    
    def _load_people(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        people = self.controller.get_all()  # Нужно добавить use case
        for person in people:
            self.tree.insert("", tk.END, values=(
                person.id,
                person.first_name,
                person.last_name,
                person.birth_date or "-"
            ))
    
    def _on_add(self):
        # Открыть форму создания
        pass
    
    def _on_edit(self):
        # Открыть форму редактирования
        pass
    
    def _on_delete(self):
        # Удалить выбранного
        pass
```

#### 4.4 Точка входа (0.5 дня)

**Файл:** `desktop/main.py`

```python
from sqlalchemy.orm import Session
from core.infrastructure.database.config import engine, SessionLocal
from desktop.app import AppContainer
from desktop.views.main_view import MainView
from desktop.controllers.person_controller import PersonController


def main():
    # Создаем сессию БД
    db: Session = SessionLocal()
    
    try:
        # Создаем контейнер с зависимостями
        container = AppContainer(db)
        
        # Создаем контроллер
        person_controller = PersonController(
            create_person=container.create_person,
            get_person=container.get_person,
            update_person=container.update_person,  # Нужно создать
            delete_person=container.delete_person   # Нужно создать
        )
        
        # Запускаем UI
        app = MainView(person_controller)
        app.mainloop()
    finally:
        db.close()


if __name__ == "__main__":
    main()
```

### Итоги этапа 4

✅ Desktop приложение использует Use Cases  
✅ Зависимости инвертированы (UI зависит от абстракций)  
✅ Легко тестировать (можно подменить репозитории на моки)  

---

## Этап 5: Добавление FastAPI (опционально) — 5-7 дней

### Цель
Добавить Web API как ещё один клиент к ядру бизнес-логики.

### Задачи

1. **Создать FastAPI приложение** (`api/main.py`)
2. **Создать роуты** (`api/routes/persons.py`, `api/routes/relationships.py`)
3. **Создать зависимости** (`api/dependencies/database.py`, `api/dependencies/auth.py`)
4. **Добавить аутентификацию** (JWT)
5. **Написать тесты**

### Пример роута

**Файл:** `api/routes/persons.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.application.dto.person_dto import CreatePersonDTO, UpdatePersonDTO
from core.application.use_cases.person.create_person import CreatePersonUseCase
from core.application.use_cases.person.get_person import GetPersonUseCase
from core.infrastructure.database.config import get_db
from api.dependencies.auth import get_current_user

router = APIRouter(prefix="/persons", tags=["Persons"])


@router.post("/")
def create_person(
    dto: CreatePersonDTO,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    repo = SQLAlchemyPersonRepository(db)
    use_case = CreatePersonUseCase(repo)
    dto.owner_id = current_user["id"]
    person = use_case.execute(dto)
    return person.to_dict()
```

---

## Этап 6: Тестирование и полировка — 3-5 дней

### Задачи

1. **Unit-тесты для Use Cases** (без БД, с моками)
2. **Integration-тесты для репозиториев** (с SQLite)
3. **E2E-тесты для API** (httpx TestClient)
4. **Настройка Alembic** для миграций
5. **Документация** (README, API docs)

### Пример unit-теста

**Файл:** `tests/unit/use_cases/test_create_person.py`

```python
from unittest.mock import Mock
from core.application.use_cases.person.create_person import CreatePersonUseCase
from core.application.dto.person_dto import CreatePersonDTO
from core.domain.entities.person import Person, Gender


def test_create_person():
    # Arrange
    mock_repo = Mock()
    use_case = CreatePersonUseCase(mock_repo)
    
    dto = CreatePersonDTO(
        first_name="Иван",
        last_name="Иванов",
        gender=Gender.MALE
    )
    
    # Act
    person = use_case.execute(dto)
    
    # Assert
    mock_repo.create.assert_called_once()
    assert person.first_name == "Иван"
    assert person.last_name == "Иванов"
```

---

## Сводная таблица этапов

| Этап | Название | Дней | Результат |
|------|----------|------|-----------|
| 0 | Подготовка | 1-2 | Структура папок, конфиги |
| 1 | Domain Layer | 2-3 | Entities, Repository Interfaces |
| 2 | Application Layer | 3-4 | Use Cases, DTO |
| 3 | Infrastructure Layer | 3-4 | SQLAlchemy Models, Repository Implementations |
| 4 | Desktop Client | 3-4 | MVC архитектура с DI |
| 5 | Web API (опц.) | 5-7 | FastAPI роуты |
| 6 | Тестирование | 3-5 | Unit/Integration/E2E тесты |
| **Итого** | | **20-29 дней** | |

---

## Риски и рекомендации

### Риски

| Риск | Как избежать |
|------|--------------|
| Нарушение Dependency Rule | Проверять импорты: `core.domain` не должен импортировать `core.infrastructure` |
| Смешивание слоёв | Каждый файл в своём разделе, ревью кода |
| Переусложнение | Начать с минимального MVP, добавлять только нужное |
| Усталость от рефакторинга | Делать поэтапно, не торопиться |

### Рекомендации

1. **Не делать всё сразу** — каждый этап завершать перед началом следующего
2. **Писать тесты параллельно** — после каждого этапа добавлять тесты
3. **Использовать type hints** — помогает IDE и снижает количество багов
4. **Частые коммиты** — после каждого рабочего этапа
5. **Ревью** — если есть кто-то, кто может посмотреть код

---

## Переход от старого кода

### Что сохраняется из `genealogy_app_plan.md`:

- Имена сущностей (Person, Relationship)
- Поля моделей
- Типы связей (father, mother, spouse, child, sibling)

### Что меняется:

| Было | Стало |
|------|-------|
| `Base = declarative_base()` | `class Base(DeclarativeBase)` |
| `Column(...)` в моделях | `Mapped[]` + `mapped_column()` |
| `session.query()` | `select()` + `session.execute()` |
| Весь UI в одном файле | MVC с разделением на Views/Controllers |
| Нет type hints | Полная типизация |
| Нет тестов | Unit/Integration тесты |
| Прямой доступ к БД | Use Cases как слой бизнес-логики |

---

## Заключение

Эта дорожная карта позволяет постепенно перейти от простого прототипа к масштабируемой архитектуре. Каждый этап независимо тестируем и может быть завершён за несколько дней. 

Ключевой принцип: **не переписывать всё сразу**, а постепенно рефакторить, сохраняя рабочую систему на каждом этапе.

---

## Итоговая оценка выполнимости

### ✅ Что исправлено в этом документе

| Было | Стало |
|------|-------|
| Старый стиль SQLAlchemy (`Column`) | Современный стиль (`Mapped[]`) |
| Pydantic v1 (`class Config`) | Pydantic v2 (`model_config`) |
| Удалён `future=True` (устарело) | Корректная конфигурация engine |
| Missing Use Cases | Добавлены Update, Delete, GetAll |
| Отсутствовала типизация в GUI | Добавлены type hints |

### 📊 Оценка для начинающего разработчика

| Уровень опыта | Реалистичный срок | Примечание |
|---------------|-------------------|------------|
| **Начинающий** (0-1 год Python) | 35-45 дней | +50% буфер на изучение |
| **Средний** (1-3 года Python) | 25-35 дней | +30% буфер |
| **Опытный** (3+ года Python) | 20-25 дней | Базовая оценка |

### ⚠️ Критические риски

| Риск | Вероятность | Как снизить |
|------|-------------|-------------|
| **Нарушение Dependency Rule** | Высокая | Проверять `grep -r "from core.infrastructure" core/domain/` |
| **Непонимание session lifecycle** | Средняя | Читать документацию SQLAlchemy, писать интеграционные тесты |
| **Переусложнение архитектуры** | Средняя | Начать с минимума, добавлять только при необходимости |
| **Выгорание от рефакторинга** | Средняя | Делать перерывы между этапами, праздновать завершение |

### 📝 Чек-лист перед стартом

- [ ] Прочитал `docs/ARCHITECTURE.md` и понял слои
- [ ] Установил Python 3.12+ и SQLAlchemy 2.0.25+
- [ ] Настроил IDE (PyCharm/VSCode) с поддержкой type hints
- [ ] Понимаю разницу между `domain` и `infrastructure`
- [ ] Протестировал простой CRUD на SQLAlchemy (мини-проект)
- [ ] Знаю, как запускать pytest и писать юнит-тесты

### 🚀 Рекомендации по выполнению

1. **Этап 0-1 (неделя 1)**: Сфокусируйся на Domain Layer — это фундамент
2. **Этап 2-3 (недели 2-3)**: Application + Infrastructure — самая сложная часть
3. **Этап 4 (неделя 4)**: Desktop клиент — уже легче, т.к. Use Cases готовы
4. **Этап 5-6 (недели 5-6)**: Опционально — API и тесты

**Не торопись.** Лучше сделать за 45 дней качественно, чем за 20 с багами.

### 📚 Полезные ресурсы

| Тема | Ресурс |
|------|--------|
| Clean Architecture | [Clean Architecture in Python (YouTube)](https://www.youtube.com/results?search_query=clean+architecture+python) |
| SQLAlchemy 2.0 | [Official Documentation](https://docs.sqlalchemy.org/en/20/) |
| Dependency Injection | [FastAPI Depends (пример DI)](https://fastapi.tiangolo.com/tutorial/dependencies/) |
| Type Hints | [PEP 484](https://peps.python.org/pep-0484/) |
| Testing | [Pytest Documentation](https://docs.pytest.org/) |

---

**Этот план выполним** при условии:
1. Посвящать проекту 1-2 часа в день
2. Не пропускать этапы тестирования
3. Задавать вопросы при блокирующих проблемах
4. Готовность переписать код, если понял, что архитектура неверна

Удачи! 🚀

