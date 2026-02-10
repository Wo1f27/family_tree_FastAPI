# Предлагаемая структура проекта

## Детальная структура файлов

```
family_tree/
│
├── core/                                    # 🎯 ОБЩЕЕ ЯДРО
│   ├── __init__.py
│   │
│   ├── domain/                              # Доменный слой
│   │   ├── __init__.py
│   │   │
│   │   ├── entities/                        # Бизнес-сущности
│   │   │   ├── __init__.py
│   │   │   ├── person.py                    # Person entity
│   │   │   ├── user.py                      # User entity
│   │   │   ├── relationship.py              # Relationship entity
│   │   │   └── event.py                     # Event entity (рождение, смерть, брак)
│   │   │
│   │   ├── repositories/                    # Интерфейсы репозиториев
│   │   │   ├── __init__.py
│   │   │   ├── person_repository.py          # IPersonRepository(ABC)
│   │   │   ├── user_repository.py           # IUserRepository(ABC)
│   │   │   └── relationship_repository.py   # IRelationshipRepository(ABC)
│   │   │
│   │   └── services/                        # Доменные сервисы
│   │       ├── __init__.py
│   │       ├── family_tree_service.py       # Логика построения дерева
│   │       └── relationship_service.py      # Логика связей
│   │
│   ├── application/                         # Слой приложения
│   │   ├── __init__.py
│   │   │
│   │   ├── use_cases/                       # Use Cases (бизнес-операции)
│   │   │   ├── __init__.py
│   │   │   ├── person/
│   │   │   │   ├── create_person.py
│   │   │   │   ├── get_person.py
│   │   │   │   ├── update_person.py
│   │   │   │   ├── delete_person.py
│   │   │   │   └── search_person.py
│   │   │   ├── user/
│   │   │   │   ├── create_user.py
│   │   │   │   ├── authenticate_user.py
│   │   │   │   └── get_user.py
│   │   │   └── relationship/
│   │   │       ├── add_relationship.py
│   │   │       ├── get_family_tree.py
│   │   │       └── remove_relationship.py
│   │   │
│   │   ├── dto/                             # Data Transfer Objects
│   │   │   ├── __init__.py
│   │   │   ├── person_dto.py
│   │   │   ├── user_dto.py
│   │   │   └── relationship_dto.py
│   │   │
│   │   └── interfaces/                      # Интерфейсы для внешних зависимостей
│   │       ├── __init__.py
│   │       ├── auth_service.py              # Интерфейс для аутентификации
│   │       └── file_storage.py              # Интерфейс для хранения файлов
│   │
│   └── infrastructure/                      # Инфраструктурный слой
│       ├── __init__.py
│       │
│       ├── database/                        # Работа с БД
│       │   ├── __init__.py
│       │   ├── config.py                    # Настройка SQLAlchemy
│       │   ├── models/                      # SQLAlchemy модели
│       │   │   ├── __init__.py
│       │   │   ├── person_model.py
│       │   │   ├── user_model.py
│       │   │   └── relationship_model.py
│       │   └── repositories/                # Реализации репозиториев
│       │       ├── __init__.py
│       │       ├── person_repository_impl.py
│       │       ├── user_repository_impl.py
│       │       └── relationship_repository_impl.py
│       │
│       ├── auth/                            # Аутентификация
│       │   ├── __init__.py
│       │   ├── jwt_service.py               # Реализация JWT
│       │   └── password_service.py          # Хеширование паролей
│       │
│       └── config/                          # Конфигурация
│           ├── __init__.py
│           └── settings.py                  # Настройки из .env
│
├── api/                                     # 🌐 WEB API (FastAPI)
│   ├── __init__.py
│   ├── main.py                             # Точка входа FastAPI
│   │
│   ├── routes/                              # API роуты
│   │   ├── __init__.py
│   │   ├── auth.py                         # /auth
│   │   ├── persons.py                      # /persons
│   │   ├── users.py                        # /users
│   │   └── relationships.py                # /relationships
│   │
│   ├── dependencies/                        # FastAPI зависимости
│   │   ├── __init__.py
│   │   ├── database.py                     # get_db()
│   │   └── auth.py                         # get_current_user()
│   │
│   ├── middleware/                          # Middleware
│   │   ├── __init__.py
│   │   └── error_handler.py                # Обработка ошибок
│   │
│   └── templates/                           # HTML шаблоны (опционально)
│       └── ...
│
├── desktop/                                 # 💻 DESKTOP приложение
│   ├── __init__.py
│   ├── main.py                             # Точка входа
│   │
│   ├── ui/                                  # UI компоненты
│   │   ├── __init__.py
│   │   ├── main_window.py                  # Главное окно
│   │   ├── person_form.py                 # Форма создания/редактирования
│   │   ├── family_tree_view.py            # Визуализация дерева
│   │   └── widgets/                        # Переиспользуемые виджеты
│   │
│   ├── views/                               # Представления (MVC)
│   │   ├── __init__.py
│   │   ├── person_view.py
│   │   └── tree_view.py
│   │
│   └── controllers/                         # Контроллеры
│       ├── __init__.py
│       ├── person_controller.py
│       └── tree_controller.py
│
├── shared/                                  # 🔄 Общие утилиты
│   ├── __init__.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── date_utils.py
│   │   └── validation.py
│   └── constants/
│       ├── __init__.py
│       └── enums.py                        # Enum'ы (типы связей и т.д.)
│
├── tests/                                   # 🧪 Тесты
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_use_cases.py
│   │   └── test_services.py
│   ├── integration/
│   │   ├── test_repositories.py
│   │   └── test_api.py
│   └── fixtures/
│       └── test_data.py
│
├── alembic/                                 # Миграции БД
│   ├── versions/
│   └── env.py
│
├── requirements/                            # Зависимости
│   ├── base.txt                            # Общие (core)
│   ├── api.txt                             # API зависимости
│   ├── desktop.txt                         # Desktop зависимости
│   └── dev.txt                             # Dev зависимости
│
├── .env.example
├── .gitignore
├── pyproject.toml
├── README.md
└── ARCHITECTURE.md
```

## Пример использования

### Use Case (core/application/use_cases/person/create_person.py)
```python
from core.domain.entities.person import Person
from core.domain.repositories.person_repository import IPersonRepository
from core.application.dto.person_dto import CreatePersonDTO

class CreatePersonUseCase:
    def __init__(self, person_repo: IPersonRepository):
        self._person_repo = person_repo
    
    def execute(self, dto: CreatePersonDTO) -> Person:
        # Бизнес-логика создания персоны
        person = Person(
            first_name=dto.first_name,
            last_name=dto.last_name,
            # ...
        )
        return self._person_repo.create(person)
```

### API Route (api/routes/persons.py)
```python
from fastapi import APIRouter, Depends
from core.application.use_cases.person.create_person import CreatePersonUseCase
from core.infrastructure.database.repositories.person_repository_impl import PersonRepositoryImpl
from api.dependencies.database import get_db

router = APIRouter(prefix="/persons", tags=["Persons"])

@router.post("/")
def create_person(dto: CreatePersonDTO, db = Depends(get_db)):
    repo = PersonRepositoryImpl(db)
    use_case = CreatePersonUseCase(repo)
    person = use_case.execute(dto)
    return person
```

### Desktop Controller (desktop/controllers/person_controller.py)
```python
from core.application.use_cases.person.create_person import CreatePersonUseCase
from core.infrastructure.database.repositories.person_repository_impl import PersonRepositoryImpl

class PersonController:
    def __init__(self, db_session):
        repo = PersonRepositoryImpl(db_session)
        self._create_person_use_case = CreatePersonUseCase(repo)
    
    def create_person(self, first_name, last_name, ...):
        dto = CreatePersonDTO(first_name=first_name, last_name=last_name, ...)
        return self._create_person_use_case.execute(dto)
```

## Преимущества

✅ **Одна бизнес-логика** - CreatePersonUseCase используется и в API, и в Desktop  
✅ **Легкое тестирование** - можно мокировать репозитории  
✅ **Гибкость** - можно менять UI/API без изменения логики  
✅ **Масштабируемость** - легко добавить Mobile клиент  
