# 📘 Руководство по созданию ядра (Core)

## Цель
Создать бизнес-ядро проекта по принципам **Clean Architecture**. Ты напишешь код самостоятельно, следуя инструкциям.

---

## 📋 Структура, которую нужно создать

```
core/
├── domain/
│   ├── entities/           # Бизнес-сущности
│   │   ├── __init__.py
│   │   ├── user.py         # Сущность User
│   │   ├── person.py       # Сущность Person
│   │   └── relationship.py # Сущность Relationship
│   └── repositories/       # Интерфейсы репозиториев
│       ├── __init__.py
│       ├── user_repository.py
│       ├── person_repository.py
│       └── relationship_repository.py
│
├── application/
│   ├── dto/                # Data Transfer Objects
│   │   ├── __init__.py
│   │   ├── user_dto.py
│   │   └── person_dto.py
│   └── use_cases/          # Бизнес-операции
│       ├── __init__.py
│       ├── user/
│       │   ├── create_user.py
│       │   ├── get_user.py
│       │   └── authenticate_user.py
│       └── person/
│           ├── create_person.py
│           └── get_person.py
│
└── infrastructure/
    ├── database/
    │   ├── models/         # SQLAlchemy модели
    │   │   ├── __init__.py
    │   │   ├── user_model.py
    │   │   └── person_model.py
    │   └── repositories/   # Реализации репозиториев
    │       ├── __init__.py
    │       ├── user_repository_impl.py
    │       └── person_repository_impl.py
    └── auth/
        ├── __init__.py
        └── password_service.py
```

---

## Шаг 1: Доменные сущности (Domain Entities)

### 📁 Файл: `core/domain/entities/user.py`

**Что это:** Бизнес-сущность пользователя. Это **чистый Python класс**, без зависимостей от SQLAlchemy, Django и т.д.

**Что должно быть:**
- Класс `User` с атрибутами: `id`, `email`, `username`, `password_hash`, `is_active`, `created_at`, `updated_at`
- Метод `__post_init__()` для валидации (проверь email на наличие `@`, username минимум 2 символа)
- Свойство `is_authenticated` (возвращает `is_active`)

**Подсказка:** Используй `@dataclass` из модуля `dataclasses`

---

### 📁 Файл: `core/domain/entities/person.py`

**Что это:** Сущность персоны в генеалогическом дереве.

**Что должно быть:**
- Класс `Person` с атрибутами: `id`, `user_id`, `first_name`, `last_name`, `middle_name`, `date_of_birth`, `date_of_death`, `gender`, `biography`
- Валидация в `__post_init__()`: имя и фамилия обязательны, дата смерти не раньше даты рождения
- Свойство `full_name` (возвращает строку: "Фамилия Имя Отчество")
- Свойство `age` (возвращает возраст в годах)
- Свойство `is_alive` (возвращает `True` если `date_of_death is None`)

---

### 📁 Файл: `core/domain/entities/relationship.py`

**Что это:** Сущность связи между двумя персонами.

**Что должно быть:**
- `Enum` `RelationshipType` со значениями: `PARENT`, `CHILD`, `SPOUSE`, `SIBLING`, `OTHER`
- Класс `Relationship` с атрибутами: `id`, `person1_id`, `person2_id`, `relationship_type`, `start_date`, `end_date`
- Валидация: персоны не могут совпадать, дата окончания не раньше даты начала
- Метод `get_reverse_type()` (для `PARENT` → `CHILD`, для `SPOUSE` → `SPOUSE` и т.д.)

---

### 📁 Файл: `core/domain/entities/__init__.py`

**Что сделать:** Экспортируй все сущности через `__all__`

**Пример:**
```python
from core.domain.entities.user import User
from core.domain.entities.person import Person
# ...

__all__ = ["User", "Person", ...]
```

---

## Шаг 2: Интерфейсы репозиториев (Repository Interfaces)

### 📁 Файл: `core/domain/repositories/user_repository.py`

**Что это:** Абстрактный класс с методами для работы с пользователями.

**Что должно быть:**
- Класс `IUserRepository` наследуется от `ABC`
- Абстрактные методы (используй `@abstractmethod`):
  - `create(user: User) -> User`
  - `get_by_id(user_id: int) -> User | None`
  - `get_by_email(email: str) -> User | None`
  - `update(user: User) -> User`
  - `delete(user_id: int) -> bool`
  - `get_all() -> list[User]`

**Подсказка:** Импортируй `ABC`, `abstractmethod` из `abc`

---

### 📁 Файл: `core/domain/repositories/person_repository.py`

**Что это:** Интерфейс для работы с персонами.

**Что должно быть:**
- Класс `IPersonRepository` наследуется от `ABC`
- Методы: `create`, `get_by_id`, `get_by_user_id`, `update`, `delete`, `search`, `get_all`

---

### 📁 Файл: `core/domain/repositories/__init__.py`

**Что сделать:** Экспортируй интерфейсы

---

## Шаг 3: DTO (Data Transfer Objects)

### 📁 Файл: `core/application/dto/user_dto.py`

**Что это:** Объекты для передачи данных между слоями.

**Что должно быть:**
- Класс `CreateUserDTO` (наследуется от `BaseModel` из Pydantic):
  - `email: str` (с валидацией email)
  - `username: str` (min_length=2)
  - `password: str` (min_length=8)

- Класс `UserResponseDTO`:
  - `id: int`, `email: str`, `username: str`, `is_active: bool`, `created_at: datetime`

**Подсказка:** Используй `Field` из `pydantic` для валидации

---

### 📁 Файл: `core/application/dto/person_dto.py`

**Что это:** DTO для персон.

**Что должно быть:**
- `CreatePersonDTO`, `UpdatePersonDTO`, `PersonResponseDTO`

---

## Шаг 4: Use Cases (Бизнес-операции)

### 📁 Файл: `core/application/use_cases/user/create_user.py`

**Что это:** Бизнес-логика создания пользователя.

**Структура:**
```python
from core.domain.entities.user import User
from core.domain.repositories.user_repository import IUserRepository
from core.application.dto.user_dto import CreateUserDTO

class CreateUserUseCase:
    def __init__(self, user_repo: IUserRepository):
        self._user_repo = user_repo
    
    def execute(self, dto: CreateUserDTO) -> User:
        # 1. Проверить, не существует ли email
        # 2. Создать сущность User
        # 3. Захешировать пароль
        # 4. Сохранить через репозиторий
        # 5. Вернуть созданного пользователя
        pass
```

---

### 📁 Файл: `core/application/use_cases/user/get_user.py`

**Что это:** Получение пользователя по ID.

**Структура:**
```python
class GetUserUseCase:
    def __init__(self, user_repo: IUserRepository):
        self._user_repo = user_repo
    
    def execute(self, user_id: int) -> User | None:
        return self._user_repo.get_by_id(user_id)
```

---

### 📁 Файл: `core/application/use_cases/user/authenticate_user.py`

**Что это:** Аутентификация пользователя (проверка пароля).

**Что должно быть:**
- Метод `execute(email: str, password: str) -> User | None`
- Проверка пароля через `PasswordService`

---

## Шаг 5: SQLAlchemy модели (Infrastructure)

### 📁 Файл: `core/infrastructure/database/models/user_model.py`

**Что это:** Модель SQLAlchemy для таблицы пользователей.

**Что должно быть:**
- Класс `UserModel` наследуется от `Base`
- Таблица `users` с колонками: `id`, `email`, `username`, `password_hash`, `is_active`, `created_at`, `updated_at`
- Метод `to_domain()` для конвертации в доменную сущность `User`

**Пример:**
```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class UserModel(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    # ... остальные колонки
    
    def to_domain(self) -> User:
        return User(
            id=self.id,
            email=self.email,
            # ...
        )
```

---

### 📁 Файл: `core/infrastructure/database/models/person_model.py`

**Что это:** Модель для таблицы персон.

**Что должно быть:**
- Класс `PersonModel` с колонками под атрибуты сущности `Person`
- Метод `to_domain()`

---

## Шаг 6: Реализации репозиториев (Infrastructure)

### 📁 Файл: `core/infrastructure/database/repositories/user_repository_impl.py`

**Что это:** Реализация `IUserRepository` через SQLAlchemy.

**Структура:**
```python
from sqlalchemy.orm import Session
from core.domain.repositories.user_repository import IUserRepository
from core.domain.entities.user import User
from core.infrastructure.database.models.user_model import UserModel

class UserRepositoryImpl(IUserRepository):
    def __init__(self, db: Session):
        self._db = db
    
    def create(self, user: User) -> User:
        # 1. Создать UserModel из User
        # 2. Добавить в сессию
        # 3. Закоммитить
        # 4. Вернуть сохранённую сущность
        pass
    
    def get_by_id(self, user_id: int) -> User | None:
        # Найти через db.query(UserModel).filter(...).first()
        # Вернуть через .to_domain()
        pass
    
    # ... реализовать остальные методы
```

---

### 📁 Файл: `core/infrastructure/database/repositories/person_repository_impl.py`

**Что это:** Реализация `IPersonRepository`.

**Аналогично:** Реализуй все методы интерфейса

---

## Шаг 7: Сервис аутентификации

### 📁 Файл: `core/infrastructure/auth/password_service.py`

**Что это:** Хеширование и проверка паролей.

**Что должно быть:**
- Функция `hash_password(password: str) -> str`
- Функция `verify_password(password: str, hashed: str) -> bool`

**Подсказка:** Используй библиотеку `bcrypt` или `passlib`

---

## 📝 Чек-лист для самопроверки

После реализации проверь:

- [ ] Все сущности используют `@dataclass`
- [ ] Интерфейсы репозиториев используют `ABC` и `@abstractmethod`
- [ ] DTO используют `BaseModel` из Pydantic
- [ ] Use Cases принимают репозитории через конструктор (Dependency Injection)
- [ ] SQLAlchemy модели имеют `to_domain()` метод
- [ ] Реализации репозиториев наследуются от интерфейсов
- [ ] Нет циклических импортов

---

## 🎯 Что дальше?

После реализации ядра:

1. **Создать API роуты** в `api/routes/` которые используют Use Cases
2. **Написать тесты** в `tests/unit/` для Use Cases
3. **Создать миграции** Alembic для новых таблиц

---

## 💡 Советы

1. **Не бойся ошибаться** — код можно исправить
2. **Смотри примеры** в `EXAMPLES.md` если застрял
3. **Запускай линтер** (если настроен) для проверки кода
4. **Тестируй по шагам** — создал сущность → проверь, создал интерфейс → проверь

---

## ❓ Вопросы для размышления

1. Почему доменные сущности не должны зависеть от SQLAlchemy?
2. Зачем нужны интерфейсы репозиториев, если можно сразу писать реализацию?
3. Что будет, если поменять местами слои (инфраструктура → домен)?

---

Удачи! Если застрянешь — смотри `EXAMPLES.md` или спрашивай.
