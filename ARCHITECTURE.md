# Архитектура проекта Family Tree

## Концепция

Проект использует **Clean Architecture** с общим ядром бизнес-логики, которое может использоваться разными клиентами:
- **Web API** (FastAPI)
- **Desktop** (PyQt/Tkinter/Electron)
- **Mobile** (в будущем - React Native/Flutter)

## Структура проекта

```
family_tree/
├── core/                          # 🎯 ОБЩЕЕ ЯДРО - бизнес-логика
│   ├── domain/                    # Доменные модели и интерфейсы
│   │   ├── entities/               # Бизнес-сущности (Person, User, Relationship)
│   │   ├── repositories/           # Интерфейсы репозиториев (абстракции)
│   │   └── services/               # Бизнес-логика (сервисы)
│   ├── application/                # Слой приложения
│   │   ├── use_cases/              # Use cases (бизнес-операции)
│   │   ├── dto/                    # Data Transfer Objects
│   │   └── interfaces/             # Интерфейсы для внешних зависимостей
│   └── infrastructure/             # Реализация инфраструктуры
│       ├── database/               # SQLAlchemy модели и репозитории
│       ├── auth/                   # Аутентификация
│       └── config/                 # Конфигурация
│
├── api/                            # 🌐 WEB API (FastAPI)
│   ├── main.py                     # Точка входа FastAPI
│   ├── routes/                     # API роуты
│   ├── dependencies/               # FastAPI зависимости
│   ├── middleware/                 # Middleware
│   └── templates/                  # HTML шаблоны (если нужны)
│
├── desktop/                        # 💻 DESKTOP приложение
│   ├── main.py                     # Точка входа
│   ├── ui/                         # UI компоненты
│   ├── views/                      # Представления
│   └── controllers/                # Контроллеры
│
├── mobile/                         # 📱 MOBILE приложение (в будущем)
│   └── ...
│
├── shared/                         # 🔄 Общие утилиты
│   ├── utils/                      # Утилиты
│   └── constants/                  # Константы
│
├── tests/                          # 🧪 Тесты
│   ├── unit/                       # Юнит-тесты
│   ├── integration/                # Интеграционные тесты
│   └── e2e/                        # End-to-end тесты
│
├── alembic/                        # Миграции БД
├── requirements/                   # Зависимости
│   ├── base.txt                    # Общие зависимости
│   ├── api.txt                     # Зависимости для API
│   ├── desktop.txt                 # Зависимости для Desktop
│   └── dev.txt                     # Dev зависимости
│
├── .env.example                    # Пример конфигурации
├── pyproject.toml                  # Конфигурация проекта
└── README.md                       # Документация

```

## Принципы архитектуры

### 1. Разделение слоев

```
┌─────────────────────────────────────┐
│   Presentation Layer (API/Desktop)   │  ← Интерфейсы пользователя
├─────────────────────────────────────┤
│   Application Layer (Use Cases)    │  ← Бизнес-операции
├─────────────────────────────────────┤
│   Domain Layer (Entities/Services)  │  ← Ядро бизнес-логики
├─────────────────────────────────────┤
│   Infrastructure Layer (DB/Auth)    │  ← Технические детали
└─────────────────────────────────────┘
```

### 2. Dependency Inversion

- **Высокоуровневые модули** (core) не зависят от низкоуровневых
- **Интерфейсы** определены в `core/domain/repositories/`
- **Реализации** находятся в `core/infrastructure/`

### 3. Пример потока данных

```
API Request → Route → Use Case → Domain Service → Repository → Database
                ↓         ↓            ↓              ↓
              DTO    Business Logic  Entity      SQLAlchemy
```

## Модули ядра (core)

### Domain Entities
- `Person` - человек в генеалогическом дереве
- `User` - пользователь системы
- `Relationship` - связь между людьми (родитель, супруг, ребенок)
- `Event` - событие (рождение, смерть, брак)

### Use Cases
- `CreatePerson` - создание персоны
- `AddRelationship` - добавление связи
- `GetFamilyTree` - получение дерева
- `SearchPerson` - поиск персоны
- `UpdatePerson` - обновление данных

### Repository Interfaces
```python
class IPersonRepository(ABC):
    @abstractmethod
    def create(self, person: Person) -> Person:
        pass
    
    @abstractmethod
    def get_by_id(self, person_id: int) -> Person | None:
        pass
    
    @abstractmethod
    def search(self, query: str) -> list[Person]:
        pass
```

## Преимущества такой архитектуры

✅ **Переиспользование кода** - одна бизнес-логика для всех клиентов  
✅ **Тестируемость** - легко мокировать репозитории  
✅ **Масштабируемость** - легко добавлять новые клиенты  
✅ **Поддерживаемость** - изменения в одном месте  
✅ **Гибкость** - можно менять БД/UI без изменения логики  

## Технологический стек

### Core
- Python 3.12+
- SQLAlchemy (ORM)
- Pydantic (валидация)
- Alembic (миграции)

### API
- FastAPI
- Uvicorn
- JWT для аутентификации

### Desktop (варианты)
- **PyQt6/PySide6** - нативный Python GUI
- **Tkinter** - встроенный в Python
- **Electron + Python Backend** - веб-технологии

### Mobile (будущее)
- React Native / Flutter
- REST API для связи с backend

## Миграция текущего проекта

Текущий код можно постепенно мигрировать:
1. Вынести модели в `core/infrastructure/database/`
2. Создать интерфейсы репозиториев в `core/domain/repositories/`
3. Перенести бизнес-логику в `core/application/use_cases/`
4. API роуты остаются в `api/routes/`, но используют use cases
