# Family Tree - Новая структура проекта

## 📁 Структура проекта

```
family_tree/
├── core/                          # 🎯 ОБЩЕЕ ЯДРО - бизнес-логика
│   ├── domain/                    # Доменный слой
│   │   ├── entities/              # Бизнес-сущности
│   │   ├── repositories/          # Интерфейсы репозиториев
│   │   └── services/              # Доменные сервисы
│   ├── application/               # Слой приложения
│   │   ├── use_cases/             # Use Cases (бизнес-операции)
│   │   │   ├── person/
│   │   │   ├── user/
│   │   │   └── relationship/
│   │   ├── dto/                   # Data Transfer Objects
│   │   └── interfaces/             # Интерфейсы для внешних зависимостей
│   └── infrastructure/            # Инфраструктурный слой
│       ├── database/              # Работа с БД
│       │   ├── models/            # SQLAlchemy модели
│       │   └── repositories/      # Реализации репозиториев
│       ├── auth/                  # Аутентификация
│       └── config/                 # Конфигурация
│
├── api/                           # 🌐 WEB API (FastAPI)
│   ├── main.py                    # Точка входа
│   ├── routes/                     # API роуты
│   ├── dependencies/               # FastAPI зависимости
│   └── middleware/                 # Middleware
│
├── desktop/                       # 💻 DESKTOP приложение
│   ├── ui/                        # UI компоненты
│   ├── views/                     # Представления
│   └── controllers/                # Контроллеры
│
├── shared/                        # 🔄 Общие утилиты
│   ├── utils/
│   └── constants/
│
├── tests/                         # 🧪 Тесты
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
└── requirements/                  # Зависимости
    ├── base.txt                   # Общие
    ├── api.txt                    # API
    ├── desktop.txt                # Desktop
    └── dev.txt                    # Dev
```

## 🚀 Быстрый старт

### Установка зависимостей

```bash
# Для API
pip install -r requirements/api.txt

# Для Desktop
pip install -r requirements/desktop.txt

# Для разработки
pip install -r requirements/dev.txt
```

### Запуск API

```bash
# Из корня проекта
python -m api.main

# Или через uvicorn
uvicorn api.main:app --reload
```

## 📝 Следующие шаги

1. **Миграция существующего кода**
   - Перенести модели из `app/modules/users/models/` в `core/infrastructure/database/models/`
   - Создать интерфейсы репозиториев в `core/domain/repositories/`
   - Вынести бизнес-логику в Use Cases

2. **Создание Use Cases**
   - Начать с модуля User как пример
   - Создать `CreateUserUseCase`, `GetUserUseCase` и т.д.

3. **Обновление API роутов**
   - Использовать Use Cases вместо прямых вызовов репозиториев

4. **Создание Desktop приложения**
   - Выбрать фреймворк (PyQt6/PySide6/Tkinter)
   - Создать базовую структуру UI

## 📚 Документация

- `ARCHITECTURE.md` - детальная архитектура
- `PROJECT_STRUCTURE.md` - структура файлов
- `EXAMPLES.md` - примеры кода
- `MIGRATION_PLAN.md` - план миграции

## ⚠️ Важно

- Старый код находится в `app/` - будет мигрирован постепенно
- Новая структура готова к использованию
- Можно работать параллельно со старой и новой структурой
