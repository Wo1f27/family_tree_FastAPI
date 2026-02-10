# Резюме: Архитектура проекта Family Tree

## 🎯 Концепция

**Общее ядро (core)** с бизнес-логикой, которое используется:
- 🌐 **Web API** (FastAPI) - уже есть
- 💻 **Desktop** приложение - нужно создать
- 📱 **Mobile** приложение - в будущем

## 📁 Структура проекта

```
family_tree/
├── core/              # 🎯 ОБЩЕЕ ЯДРО - бизнес-логика
│   ├── domain/       # Сущности, интерфейсы репозиториев
│   ├── application/  # Use Cases, DTO
│   └── infrastructure/ # Реализация (БД, аутентификация)
│
├── api/              # 🌐 FastAPI веб-приложение
│   └── routes/       # API эндпоинты (используют Use Cases)
│
├── desktop/          # 💻 Desktop приложение
│   └── controllers/  # Контроллеры (используют те же Use Cases)
│
└── shared/           # 🔄 Общие утилиты
```

## ✨ Преимущества

✅ **Одна бизнес-логика** - не дублируется код  
✅ **Легко тестировать** - можно мокировать репозитории  
✅ **Масштабируемо** - легко добавить Mobile клиент  
✅ **Гибко** - можно менять UI/БД без изменения логики  

## 🔄 Как это работает

### Пример: Создание персоны

**1. Use Case (core)** - бизнес-логика:
```python
class CreatePersonUseCase:
    def execute(self, dto: CreatePersonDTO) -> Person:
        # Валидация, бизнес-правила
        person = Person(...)
        return self._repo.create(person)
```

**2. API Route** - использует Use Case:
```python
@router.post("/persons")
def create_person(dto: CreatePersonDTO):
    use_case = CreatePersonUseCase(repo)
    return use_case.execute(dto)
```

**3. Desktop Controller** - использует тот же Use Case:
```python
def create_person(self, form_data):
    use_case = CreatePersonUseCase(repo)
    return use_case.execute(dto)
```

**Одна логика → три интерфейса!**

## 🛠 Технологии

### Core
- Python 3.12+
- SQLAlchemy (ORM)
- Pydantic (валидация)

### API
- FastAPI
- JWT аутентификация

### Desktop (варианты)
- **PyQt6/PySide6** - нативный Python GUI (рекомендую)
- **Tkinter** - простой, встроенный
- **Electron** - веб-технологии

## 📋 План действий

1. **Создать структуру** директорий
2. **Мигрировать** текущий код в core
3. **Создать Use Cases** для бизнес-логики
4. **Обновить API** для использования Use Cases
5. **Создать Desktop** приложение

Подробности в файлах:
- `ARCHITECTURE.md` - детальная архитектура
- `PROJECT_STRUCTURE.md` - структура файлов
- `EXAMPLES.md` - примеры кода
- `MIGRATION_PLAN.md` - план миграции

## ❓ Вопросы для решения

1. **Desktop фреймворк?** PyQt6, Tkinter или Electron?
2. **Синхронизация?** Локальная БД или API для Desktop?
3. **Приоритеты?** Сначала Web, Desktop или параллельно?

---

**Готов начать миграцию?** Начнем с создания структуры и миграции одного модуля (User) как пример!
