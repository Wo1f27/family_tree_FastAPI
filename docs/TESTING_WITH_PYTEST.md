# Тестирование проекта на Pytest

## Структура тестов

```
tests/
├── __init__.py
├── conftest.py                    # Общие fixtures и конфигурация
├── unit/                          # Юнит-тесты (быстрые, без БД)
│   ├── __init__.py
│   ├── test_entities/
│   │   ├── __init__.py
│   │   ├── test_user.py
│   │   ├── test_person.py
│   │   └── test_relationship.py
│   ├── test_use_cases/
│   │   ├── __init__.py
│   │   ├── test_user/
│   │   │   ├── test_create_user.py
│   │   │   └── test_get_user.py
│   │   └── test_person/
│   │       ├── test_create_person.py
│   │       └── test_get_person.py
│   └── test_services/
│       ├── __init__.py
│       ├── test_password_service.py
│       └── test_jwt_service.py
├── integration/                   # Интеграционные тесты (с БД)
│   ├── __init__.py
│   ├── test_repositories/
│   │   ├── __init__.py
│   │   ├── test_user_repository.py
│   │   ├── test_person_repository.py
│   │   └── test_relationship_repository.py
│   └── test_api/
│       ├── __init__.py
│       ├── test_auth.py
│       ├── test_persons.py
│       └── test_users.py
├── fixtures/                      # Тестовые данные
│   ├── __init__.py
│   ├── test_data.py
│   └── database_fixtures.py
└── e2e/                           # End-to-End тесты (опционально)
    ├── __init__.py
    └── test_full_workflow.py
```

---

## Конфигурация Pytest

### `pyproject.toml` (добавить секцию)

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--strict-markers",
    "--tb=short",
    "--cov=core",
    "--cov=api",
    "--cov-report=html",
    "--cov-report=term-missing",
]
markers = [
    "unit: Юнит-тесты",
    "integration: Интеграционные тесты",
    "slow: Медленные тесты",
    "db: Тесты с базой данных",
]
```

### `requirements/dev.txt` (добавить)

```
-r base.txt
-r api.txt
-r desktop.txt

# Тестирование
pytest==8.3.4
pytest-asyncio==0.23.3
pytest-cov==5.0.0
pytest-mock==3.14.0
pytest-xdist==3.6.1
factory-boy==3.3.0
faker==24.0.0
```

---

## Общие fixtures

### `tests/conftest.py`

```python
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from core.infrastructure.database.models.base import Base
from core.infrastructure.database.config import DatabaseConfig


# ==================== SYNCHRONOUS DB (для unit/integration тестов) ====================

@pytest.fixture(scope="session")
def sqlite_engine():
    """Создание in-memory SQLite движка для тестов"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(sqlite_engine) -> Generator[Session, None, None]:
    """Сессия БД для тестов"""
    SessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=sqlite_engine
    )
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# ==================== ASYNCHRONOUS DB (для API тестов) ====================

@pytest.fixture(scope="session")
def event_loop():
    """Event loop для async тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_engine():
    """Async движок для тестов API"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def async_db_session(async_engine) -> AsyncGenerator[AsyncSession, None]:
    """Async сессия БД для тестов API"""
    async_session = async_sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


# ==================== MARKERS ====================

def pytest_configure(config):
    config.addinivalue_line("markers", "unit: Юнит-тесты")
    config.addinivalue_line("markers", "integration: Интеграционные тесты")
    config.addinivalue_line("markers", "db: Тесты с базой данных")
```

---

## Фикстуры тестовых данных

### `tests/fixtures/test_data.py`

```python
from datetime import date, datetime
from typing import Generator

from core.domain.entities.user import User
from core.domain.entities.person import Person
from core.domain.entities.relationship import Relationship, RelationshipType


# ==================== USER FACTORY ====================

def create_user(
    id: int = 1,
    email: str = "test@example.com",
    username: str = "testuser",
    password_hash: str = "hashed_password_123",
    is_active: bool = True,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> User:
    """Factory для создания тестового пользователя"""
    return User(
        id=id,
        email=email,
        username=username,
        password_hash=password_hash,
        is_active=is_active,
        created_at=created_at or datetime(2024, 1, 1),
        updated_at=updated_at or datetime(2024, 1, 1),
    )


# ==================== PERSON FACTORY ====================

def create_person(
    id: int = 1,
    user_id: int | None = 1,
    first_name: str = "Иван",
    last_name: str = "Иванов",
    middle_name: str | None = "Иванович",
    date_of_birth: date | None = date(1990, 1, 1),
    date_of_death: date | None = None,
    gender: str | None = "male",
    biography: str | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> Person:
    """Factory для создания тестовой персоны"""
    return Person(
        id=id,
        user_id=user_id,
        first_name=first_name,
        last_name=last_name,
        middle_name=middle_name,
        date_of_birth=date_of_birth,
        date_of_death=date_of_death,
        gender=gender,
        biography=biography,
        created_at=created_at or datetime(2024, 1, 1),
        updated_at=updated_at or datetime(2024, 1, 1),
    )


# ==================== RELATIONSHIP FACTORY ====================

def create_relationship(
    id: int = 1,
    person1_id: int = 1,
    person2_id: int = 2,
    relationship_type: RelationshipType = RelationshipType.PARENT,
    start_date: date | None = None,
    end_date: date | None = None,
    created_at: datetime | None = None,
) -> Relationship:
    """Factory для создания тестовой связи"""
    return Relationship(
        id=id,
        person1_id=person1_id,
        person2_id=person2_id,
        relationship_type=relationship_type,
        start_date=start_date,
        end_date=end_date,
        created_at=created_at or datetime(2024, 1, 1),
    )
```

---

## Юнит-тесты

### `tests/unit/test_entities/test_user.py`

```python
import pytest
from datetime import datetime
from core.domain.entities.user import User


class TestUserEntity:
    """Тесты для User entity"""

    def test_user_creation(self):
        """Тест создания пользователя"""
        user = User(
            id=1,
            email="test@example.com",
            username="testuser",
            password_hash="hash123",
        )
        
        assert user.id == 1
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.is_active is True

    def test_user_email_validation(self):
        """Тест валидации email"""
        with pytest.raises(ValueError, match="Некорректный email"):
            User(
                id=1,
                email="invalid-email",
                username="testuser",
                password_hash="hash123",
            )

    def test_user_username_min_length(self):
        """Тест минимальной длины username"""
        with pytest.raises(ValueError, match="Username минимум 2 символа"):
            User(
                id=1,
                email="test@example.com",
                username="a",
                password_hash="hash123",
            )

    def test_is_authenticated_property(self):
        """Тест свойства is_authenticated"""
        active_user = User(
            id=1,
            email="test@example.com",
            username="testuser",
            password_hash="hash123",
            is_active=True,
        )
        assert active_user.is_authenticated is True

        inactive_user = User(
            id=1,
            email="test@example.com",
            username="testuser",
            password_hash="hash123",
            is_active=False,
        )
        assert inactive_user.is_authenticated is False
```

### `tests/unit/test_entities/test_person.py`

```python
import pytest
from datetime import date
from core.domain.entities.person import Person


class TestPersonEntity:
    """Тесты для Person entity"""

    def test_person_creation(self):
        """Тест создания персоны"""
        person = Person(
            id=1,
            first_name="Иван",
            last_name="Иванов",
            date_of_birth=date(1990, 1, 1),
        )
        
        assert person.id == 1
        assert person.first_name == "Иван"
        assert person.last_name == "Иванов"

    def test_full_name_property(self):
        """Тест свойства full_name"""
        person = Person(
            id=1,
            first_name="Иван",
            last_name="Иванов",
            middle_name="Иванович",
        )
        assert person.full_name == "Иванов Иван Иванович"

    def test_age_calculation(self):
        """Тест расчёта возраста"""
        person = Person(
            id=1,
            first_name="Иван",
            last_name="Иванов",
            date_of_birth=date(1990, 1, 1),
        )
        age = person.age
        assert age >= 34  # Зависит от текущей даты

    def test_age_after_death(self):
        """Тест возраста после смерти"""
        person = Person(
            id=1,
            first_name="Иван",
            last_name="Иванов",
            date_of_birth=date(1990, 1, 1),
            date_of_death=date(2020, 1, 1),
        )
        assert person.age == 30
        assert person.is_alive is False

    def test_person_without_name_raises(self):
        """Тест валидации имени"""
        with pytest.raises(ValueError, match="Имя и фамилия обязательны"):
            Person(
                id=1,
                first_name="",
                last_name="",
            )

    def test_death_before_birth_raises(self):
        """Тест валидации дат смерти и рождения"""
        with pytest.raises(ValueError, match="Дата смерти не может быть раньше"):
            Person(
                id=1,
                first_name="Иван",
                last_name="Иванов",
                date_of_birth=date(2000, 1, 1),
                date_of_death=date(1990, 1, 1),
            )
```

### `tests/unit/test_entities/test_relationship.py`

```python
import pytest
from datetime import date
from core.domain.entities.relationship import Relationship, RelationshipType


class TestRelationshipEntity:
    """Тесты для Relationship entity"""

    def test_relationship_creation(self):
        """Тест создания связи"""
        rel = Relationship(
            id=1,
            person1_id=1,
            person2_id=2,
            relationship_type=RelationshipType.PARENT,
        )
        
        assert rel.id == 1
        assert rel.person1_id == 1
        assert rel.person2_id == 2
        assert rel.relationship_type == RelationshipType.PARENT

    def test_self_relationship_raises(self):
        """Тест связи с самой собой"""
        with pytest.raises(ValueError, match="не может быть связана сама с собой"):
            Relationship(
                id=1,
                person1_id=1,
                person2_id=1,  # Та же персона
                relationship_type=RelationshipType.PARENT,
            )

    def test_reverse_relationship_type(self):
        """Тест обратного типа связи"""
        parent_rel = Relationship(
            id=1,
            person1_id=1,
            person2_id=2,
            relationship_type=RelationshipType.PARENT,
        )
        assert parent_rel.get_reverse_type() == RelationshipType.CHILD

        child_rel = Relationship(
            id=1,
            person1_id=1,
            person2_id=2,
            relationship_type=RelationshipType.CHILD,
        )
        assert child_rel.get_reverse_type() == RelationshipType.PARENT

        spouse_rel = Relationship(
            id=1,
            person1_id=1,
            person2_id=2,
            relationship_type=RelationshipType.SPOUSE,
        )
        assert spouse_rel.get_reverse_type() == RelationshipType.SPOUSE

    def test_end_date_before_start_raises(self):
        """Тест валидации дат"""
        with pytest.raises(ValueError, match="Дата окончания не может быть раньше"):
            Relationship(
                id=1,
                person1_id=1,
                person2_id=2,
                relationship_type=RelationshipType.SPOUSE,
                start_date=date(2020, 1, 1),
                end_date=date(2010, 1, 1),
            )
```

---

## Юнит-тесты Use Cases

### `tests/unit/test_use_cases/test_person/test_create_person.py`

```python
import pytest
from unittest.mock import Mock
from core.application.use_cases.person.create_person import CreatePersonUseCase
from core.application.dto.person_dto import CreatePersonDTO


class TestCreatePersonUseCase:
    """Тесты для CreatePersonUseCase"""

    @pytest.fixture
    def mock_repo(self):
        """Mock репозитория"""
        return Mock()

    @pytest.fixture
    def use_case(self, mock_repo):
        """Use case с моковым репозиторием"""
        return CreatePersonUseCase(mock_repo)

    def test_create_person_success(self, use_case, mock_repo):
        """Тест успешного создания персоны"""
        # Arrange
        dto = CreatePersonDTO(
            first_name="Иван",
            last_name="Иванов",
            middle_name="Иванович",
        )
        
        expected_person = Mock()
        expected_person.id = 1
        mock_repo.create.return_value = expected_person

        # Act
        result = use_case.execute(dto)

        # Assert
        mock_repo.create.assert_called_once()
        assert result == expected_person

    def test_create_person_with_birth_date(self, use_case, mock_repo):
        """Тест создания персоны с датой рождения"""
        from datetime import date
        
        dto = CreatePersonDTO(
            first_name="Иван",
            last_name="Иванов",
            date_of_birth=date(1990, 1, 1),
        )
        
        mock_repo.create.return_value = Mock(id=1)
        
        result = use_case.execute(dto)
        
        # Проверка, что в репозиторий передана правильная дата
        call_args = mock_repo.create.call_args[0][0]
        assert call_args.date_of_birth == date(1990, 1, 1)
```

### `tests/unit/test_use_cases/test_user/test_create_user.py`

```python
import pytest
from unittest.mock import Mock, patch
from core.application.use_cases.user.create_user import CreateUserUseCase
from core.application.dto.user_dto import CreateUserDTO


class TestCreateUserUseCase:
    """Тесты для CreateUserUseCase"""

    @pytest.fixture
    def mock_repo(self):
        return Mock()

    @pytest.fixture
    def use_case(self, mock_repo):
        return CreateUserUseCase(mock_repo)

    def test_create_user_success(self, use_case, mock_repo):
        """Тест успешного создания пользователя"""
        # Arrange
        dto = CreateUserDTO(
            email="test@example.com",
            username="testuser",
            password="password123",
        )
        
        expected_user = Mock()
        expected_user.id = 1
        mock_repo.get_by_email.return_value = None
        mock_repo.get_by_username.return_value = None
        mock_repo.create.return_value = expected_user

        # Act
        result = use_case.execute(dto)

        # Assert
        mock_repo.get_by_email.assert_called_once_with("test@example.com")
        mock_repo.get_by_username.assert_called_once_with("testuser")
        mock_repo.create.assert_called_once()
        assert result == expected_user

    def test_create_user_duplicate_email(self, use_case, mock_repo):
        """Тест создания с дублирующимся email"""
        # Arrange
        dto = CreateUserDTO(
            email="test@example.com",
            username="testuser",
            password="password123",
        )
        
        existing_user = Mock(id=1)
        mock_repo.get_by_email.return_value = existing_user

        # Act & Assert
        with pytest.raises(ValueError, match="Email.*уже занят"):
            use_case.execute(dto)

    def test_create_user_duplicate_username(self, use_case, mock_repo):
        """Тест создания с дублирующимся username"""
        # Arrange
        dto = CreateUserDTO(
            email="test@example.com",
            username="testuser",
            password="password123",
        )
        
        mock_repo.get_by_email.return_value = None
        mock_repo.get_by_username.return_value = Mock(id=1)

        # Act & Assert
        with pytest.raises(ValueError, match="Username.*уже занят"):
            use_case.execute(dto)

    @patch('core.application.use_cases.user.create_user.hash_password')
    def test_create_user_password_hashed(self, mock_hash, use_case, mock_repo):
        """Тест хеширования пароля"""
        # Arrange
        mock_hash.return_value = "hashed_password"
        dto = CreateUserDTO(
            email="test@example.com",
            username="testuser",
            password="password123",
        )
        mock_repo.get_by_email.return_value = None
        mock_repo.get_by_username.return_value = None
        
        expected_user = Mock(id=1)
        mock_repo.create.return_value = expected_user

        # Act
        use_case.execute(dto)

        # Assert
        mock_hash.assert_called_once_with("password123")
```

---

## Интеграционные тесты

### `tests/integration/test_repositories/test_user_repository.py`

```python
import pytest
from sqlalchemy import select

from core.infrastructure.database.repositories.sqlite_user_repository import SQLiteUserRepositoryImpl
from core.domain.entities.user import User
from core.infrastructure.database.models.user_model import UserModel


@pytest.mark.integration
@pytest.mark.db
class TestUserRepositoryIntegration:
    """Интеграционные тесты для UserRepository"""

    def test_create_user(self, db_session):
        """Тест создания пользователя через репозиторий"""
        # Arrange
        repo = SQLiteUserRepositoryImpl(db_session)
        user = User(
            id=None,
            email="test@example.com",
            username="testuser",
            password_hash="hashed_password_123",
        )

        # Act
        result = repo.create(user)

        # Assert
        assert result.id is not None
        assert result.email == "test@example.com"
        assert result.username == "testuser"

        # Проверка в БД
        stored = db_session.execute(
            select(UserModel).where(UserModel.id == result.id)
        ).scalar_one_or_none()
        assert stored is not None
        assert stored.email == "test@example.com"

    def test_get_by_id(self, db_session):
        """Тест получения пользователя по ID"""
        # Arrange
        repo = SQLiteUserRepositoryImpl(db_session)
        user = User(
            id=None,
            email="test@example.com",
            username="testuser",
            password_hash="hash",
        )
        created = repo.create(user)

        # Act
        result = repo.get_by_id(created.id)

        # Assert
        assert result is not None
        assert result.id == created.id
        assert result.email == "test@example.com"

    def test_get_by_id_not_found(self, db_session):
        """Тест получения несуществующего пользователя"""
        repo = SQLiteUserRepositoryImpl(db_session)
        result = repo.get_by_id(99999)
        assert result is None

    def test_get_by_email(self, db_session):
        """Тест получения пользователя по email"""
        repo = SQLiteUserRepositoryImpl(db_session)
        user = User(
            id=None,
            email="test@example.com",
            username="testuser",
            password_hash="hash",
        )
        created = repo.create(user)

        result = repo.get_by_email("test@example.com")
        assert result is not None
        assert result.id == created.id

    def test_update_user(self, db_session):
        """Тест обновления пользователя"""
        repo = SQLiteUserRepositoryImpl(db_session)
        user = User(
            id=None,
            email="test@example.com",
            username="testuser",
            password_hash="hash",
        )
        created = repo.create(user)

        # Обновление
        created.username = "newusername"
        updated = repo.update(created)

        assert updated.username == "newusername"

    def test_delete_user(self, db_session):
        """Тест удаления пользователя"""
        repo = SQLiteUserRepositoryImpl(db_session)
        user = User(
            id=None,
            email="test@example.com",
            username="testuser",
            password_hash="hash",
        )
        created = repo.create(user)

        result = repo.delete(created.id)
        assert result is True

        # Проверка удаления
        assert repo.get_by_id(created.id) is None

    def test_delete_user_not_found(self, db_session):
        """Тест удаления несуществующего пользователя"""
        repo = SQLiteUserRepositoryImpl(db_session)
        result = repo.delete(99999)
        assert result is False

    def test_get_all_with_pagination(self, db_session):
        """Тест получения всех пользователей с пагинацией"""
        repo = SQLiteUserRepositoryImpl(db_session)
        
        # Создание тестовых данных
        for i in range(5):
            user = User(
                id=None,
                email=f"user{i}@example.com",
                username=f"user{i}",
                password_hash="hash",
            )
            repo.create(user)

        # Пагинация
        all_users = repo.get_all(skip=0, limit=100)
        assert len(all_users) == 5

        skipped = repo.get_all(skip=2, limit=100)
        assert len(skipped) == 3
```

### `tests/integration/test_repositories/test_person_repository.py`

```python
import pytest
from datetime import date

from core.infrastructure.database.repositories.sqlite_person_repository import SQLitePersonRepositoryImpl
from core.domain.entities.person import Person


@pytest.mark.integration
@pytest.mark.db
class TestPersonRepositoryIntegration:
    """Интеграционные тесты для PersonRepository"""

    def test_create_person(self, db_session):
        """Тест создания персоны"""
        repo = SQLitePersonRepositoryImpl(db_session)
        person = Person(
            id=None,
            first_name="Иван",
            last_name="Иванов",
            date_of_birth=date(1990, 1, 1),
        )

        result = repo.create(person)

        assert result.id is not None
        assert result.first_name == "Иван"
        assert result.last_name == "Иванов"

    def test_search_person(self, db_session):
        """Тест поиска персон"""
        repo = SQLitePersonRepositoryImpl(db_session)
        
        # Создание тестовых данных
        repo.create(Person(
            id=None,
            first_name="Иван",
            last_name="Иванов",
        ))
        repo.create(Person(
            id=None,
            first_name="Петр",
            last_name="Петров",
        ))

        # Поиск
        results = repo.search("Иван")
        assert len(results) == 1
        assert results[0].first_name == "Иван"

    def test_get_by_user_id(self, db_session):
        """Тест получения персон по user_id"""
        repo = SQLitePersonRepositoryImpl(db_session)
        
        repo.create(Person(
            id=None,
            user_id=1,
            first_name="Иван",
            last_name="Иванов",
        ))
        repo.create(Person(
            id=None,
            user_id=2,
            first_name="Петр",
            last_name="Петров",
        ))

        user1_persons = repo.get_by_user_id(1)
        assert len(user1_persons) == 1
        assert user1_persons[0].first_name == "Иван"
```

---

## Интеграционные тесты API

### `tests/integration/test_api/test_persons.py`

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.main import app


@pytest.mark.integration
@pytest.mark.db
class TestPersonsAPI:
    """Интеграционные тесты API персон"""

    @pytest.fixture
    def client(self, async_db_session: AsyncSession):
        """TestClient для FastAPI"""
        # Mock зависимости get_db
        from api.dependencies.database import get_db
        
        async def override_get_db():
            yield async_db_session
        
        app.dependency_overrides[get_db] = override_get_db
        
        with TestClient(app) as client:
            yield client
        
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_person(self, client, async_db_session: AsyncSession):
        """Тест создания персоны через API"""
        payload = {
            "first_name": "Иван",
            "last_name": "Иванов",
            "middle_name": "Иванович",
            "date_of_birth": "1990-01-01",
        }

        response = client.post("/api/persons/", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == "Иван"
        assert data["last_name"] == "Иванов"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_get_person(self, client, async_db_session: AsyncSession):
        """Тест получения персоны"""
        # Сначала создаём
        create_payload = {
            "first_name": "Иван",
            "last_name": "Иванов",
        }
        create_response = client.post("/api/persons/", json=create_payload)
        person_id = create_response.json()["id"]

        # Затем получаем
        response = client.get(f"/api/persons/{person_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == person_id

    @pytest.mark.asyncio
    async def test_get_person_not_found(self, client):
        """Тест получения несуществующей персоны"""
        response = client.get("/api/persons/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_person(self, client, async_db_session: AsyncSession):
        """Тест удаления персоны"""
        # Создаём
        create_payload = {"first_name": "Иван", "last_name": "Иванов"}
        create_response = client.post("/api/persons/", json=create_payload)
        person_id = create_response.json()["id"]

        # Удаляем
        response = client.delete(f"/api/persons/{person_id}")
        assert response.status_code == 200

        # Проверяем, что удалена
        get_response = client.get(f"/api/persons/{person_id}")
        assert get_response.status_code == 404
```

---

## Запуск тестов

### Базовые команды

```bash
# Запустить все тесты
pytest

# Запустить только unit тесты
pytest -m unit

# Запустить только integration тесты
pytest -m integration

# Запустить тесты с покрытием
pytest --cov=core --cov=api --cov-report=html

# Запустить конкретный файл
pytest tests/unit/test_entities/test_person.py

# Запустить конкретный тест
pytest tests/unit/test_entities/test_person.py::TestPersonEntity::test_person_creation

# Запустить в режиме watch (авторенонс)
pytest --looponfail

# Параллельный запуск (ускорение)
pytest -n auto

# Тесты только для API
pytest tests/integration/test_api/

# Вывод только ошибок
pytest -v --tb=short
```

### CI/CD интеграция

`.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install -r requirements/dev.txt
      
      - name: Run tests
        run: |
          pytest --cov=core --cov=api --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Рекомендации по тестированию

| Тип теста | Когда использовать | Скорость | Изоляция |
|-----------|-------------------|----------|----------|
| **Unit** | Логика entities, use cases | Быстро (<1s) | Полная (mocks) |
| **Integration** | Репозитории, БД | Средне | Частичная (БД) |
| **E2E** | Полный сценарий | Медленно | Нет (всё вместе) |

### Принципы хорошего теста

1. **Один тест — одна проверка**
2. **Именование**: `test_{действие}_{ожидаемый_результат}`
3. **Изоляция**: каждый тест независим
4. **Детерминизм**: нет рандома, фиксированные данные
5. **Читаемость**: явные assertions, понятные сообщения

### Что тестировать в первую очередь

- [x] Доменные сущности (валидация, свойства)
- [x] Use Cases (бизнес-логика)
- [x] Репозитории (CRUD операции)
- [ ] API endpoints (интеграция)
- [ ] Desktop UI (опционально, сложно)

---

## Заключение

Pytest обеспечивает:
- ✅ Простой синтаксис тестов
- ✅ Автоматический discovery тестов
- ✅/fixtures для переиспользования кода
- ✅ Плагины для покрытия, async, параллелизма
- ✅ Интеграцию с CI/CD

Этот файл содержит полную реализацию тестов для проекта Family Tree.
