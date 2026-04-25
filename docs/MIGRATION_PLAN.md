# План миграции проекта на новую архитектуру

## Текущее состояние

Проект имеет структуру:
```
app/
├── modules/
│   ├── auth/
│   ├── users/
│   └── person_card/ (пустой)
├── db/
├── templates/
└── main.py
```

## Цель миграции

Реорганизовать проект в структуру с общим ядром:
```
core/          - бизнес-логика
api/           - FastAPI приложение
desktop/       - Desktop приложение
```

## Этапы миграции

### Этап 1: Подготовка структуры (1-2 дня)

1. **Создать новую структуру директорий**
   ```bash
   mkdir -p core/domain/{entities,repositories,services}
   mkdir -p core/application/{use_cases,dto,interfaces}
   mkdir -p core/infrastructure/{database,auth,config}
   mkdir -p api/{routes,dependencies,middleware}
   mkdir -p desktop/{ui,views,controllers}
   mkdir -p shared/{utils,constants}
   ```

2. **Создать базовые файлы**
   - `core/__init__.py`
   - `api/__init__.py`
   - `desktop/__init__.py`
   - Обновить `requirements/` структуру

3. **Настроить импорты**
   - Обновить `pyproject.toml` или `setup.py`
   - Настроить пути импорта

### Этап 2: Миграция моделей и репозиториев (2-3 дня)

1. **Перенести модели в core/infrastructure/database/models/**
   - `app/modules/users/models/users.py` → `core/infrastructure/database/models/user_model.py`
   - Создать `person_model.py` для генеалогического дерева

2. **Создать интерфейсы репозиториев в core/domain/repositories/**
   - `IUserRepository`
   - `IPersonRepository`
   - `IProfileRepository`

3. **Перенести реализации репозиториев**
   - `app/modules/users/repository/*` → `core/infrastructure/database/repositories/*`
   - Адаптировать под интерфейсы

4. **Исправить найденные баги**
   - Исправить работу с Pydantic моделями в `profiles.py`
   - Убрать дублирование кода

### Этап 3: Создание Use Cases (2-3 дня)

1. **Вынести бизнес-логику из operators в Use Cases**
   - `CreateUserUseCase`
   - `GetUserUseCase`
   - `UpdateUserUseCase`
   - `DeleteUserUseCase`
   - `AuthenticateUserUseCase`

2. **Создать DTO**
   - Перенести entities в `core/application/dto/`
   - Адаптировать под новую структуру

3. **Создать доменные сервисы (если нужно)**
   - `FamilyTreeService` - для построения дерева
   - `RelationshipService` - для работы со связями

### Этап 4: Рефакторинг API (2-3 дня)

1. **Обновить роуты в api/routes/**
   - Использовать Use Cases вместо прямых вызовов репозиториев
   - Обновить зависимости

2. **Перенести аутентификацию**
   - `app/modules/auth/*` → `core/infrastructure/auth/`
   - Создать `api/dependencies/auth.py`

3. **Обновить main.py**
   - Перенести в `api/main.py`
   - Обновить импорты

4. **Обновить шаблоны (если нужны)**
   - Исправить Django-синтаксис на Jinja2

### Этап 5: Создание Desktop приложения (3-5 дней)

1. **Выбрать фреймворк**
   - PyQt6/PySide6 (рекомендую)
   - Tkinter (проще, но менее функциональный)
   - Electron + Python Backend

2. **Создать базовую структуру**
   - Главное окно
   - Контроллеры (используют те же Use Cases)
   - UI компоненты

3. **Реализовать основные функции**
   - Список персон
   - Создание/редактирование
   - Визуализация дерева

### Этап 6: Тестирование и документация (2-3 дня)

1. **Написать тесты**
   - Unit тесты для Use Cases
   - Integration тесты для репозиториев
   - E2E тесты для API

2. **Обновить документацию**
   - README.md
   - API документация
   - Руководство разработчика

## Пошаговая инструкция для начала

### Шаг 1: Создать структуру

```bash
# В корне проекта
mkdir -p core/domain/{entities,repositories,services}
mkdir -p core/application/{use_cases,dto,interfaces}
mkdir -p core/infrastructure/{database/{models,repositories},auth,config}
mkdir -p api/{routes,dependencies,middleware}
mkdir -p desktop/{ui,views,controllers}
mkdir -p shared/{utils,constants}
mkdir -p tests/{unit,integration,fixtures}
```

### Шаг 2: Создать базовые __init__.py

Создать `__init__.py` во всех новых директориях.

### Шаг 3: Начать с одного модуля (User)

1. Создать интерфейс `IUserRepository`
2. Перенести модель `User`
3. Создать реализацию репозитория
4. Создать Use Cases
5. Обновить API роуты

### Шаг 4: Повторить для других модулей

После успешной миграции User, повторить для Profile и Person.

## Важные моменты

⚠️ **Не ломать существующий функционал**
- Мигрировать постепенно
- Тестировать после каждого этапа
- Можно оставить старый код параллельно на время миграции

⚠️ **База данных**
- Миграции Alembic нужно обновить
- Возможно, потребуется создать новые миграции

⚠️ **Зависимости**
- Разделить на `requirements/base.txt`, `requirements/api.txt`, `requirements/desktop.txt`

## Оценка времени

- **Минимальная миграция** (только структура + один модуль): 3-5 дней
- **Полная миграция** (все модули + Desktop): 2-3 недели
- **С тестами и документацией**: 3-4 недели

## Рекомендации

1. **Начать с малого** - мигрировать один модуль (User) полностью
2. **Использовать Git** - делать коммиты после каждого этапа
3. **Тестировать** - писать тесты параллельно с миграцией
4. **Документировать** - фиксировать изменения в процессе

## Вопросы для обсуждения

1. Какой фреймворк выбрать для Desktop?
   - PyQt6 (мощный, но требует лицензию для коммерции)
   - PySide6 (то же, но LGPL)
   - Tkinter (простой, встроенный)
   - Electron (веб-технологии)

2. Нужна ли синхронизация между Desktop и Web?
   - Локальная БД для Desktop?
   - API для Desktop?
   - Гибридный подход?

3. Приоритеты разработки:
   - Сначала Web API?
   - Параллельно Desktop?
   - Сначала ядро?
