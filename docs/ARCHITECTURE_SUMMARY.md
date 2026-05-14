# Резюме: архитектура Family Tree

## Сейчас и цель

| | |
|--|--|
| **Сейчас (репозиторий)** | Один процесс: **Python 3.13+**, **SQLAlchemy 2.0+**, **SQLite**, **Tkinter** — файлы в корне: `main.py` → `gui.py`, плюс `models.py`, `database.py`, данные в `data/genealogy.db`. Это **фаза A** в [MVP_TASK_PLAN.md](MVP_TASK_PLAN.md) (рабочий baseline для обучения). |
| **Цель** | Тот же продукт постепенно вырастает до **Clean Architecture**: общее ядро `core/` (domain → application → infrastructure), поверх него **несколько клиентов** — по желанию **FastAPI** и/или улучшенный Desktop. |

## Концепция целевой системы

**Общее ядро (`core/`)** с бизнес-логикой, которое могут использовать:

- **Desktop (Tkinter)** — основной клиент для обучения в этом проекте; идёт в комплекте с Python, отдельной версии «пакета Tkinter» нет.
- **Web API (FastAPI)** — второй клиент, когда дойдёте до фазы **D** (см. [MVP_TASK_PLAN.md](MVP_TASK_PLAN.md) §0.1).
- **Mobile** — опционально в долгую перспективу.

## Структура проекта (целевая)

```
family_tree/
├── core/                    # ядро: domain, application, infrastructure
├── api/                     # FastAPI (появится на фазе D)
├── desktop/                 # или ui/: Tkinter-views, тонкий слой (фазы B–C)
├── shared/                  # общие утилиты (по необходимости)
└── tests/
```

Текущий **плоский** вариант (`gui.py` рядом с `models.py`) — нормальная стартовая точка; разнесение по папкам описано в [mvp-guide/](mvp-guide/README.md).

## Преимущества целевой схемы

- Одна бизнес-логика (use cases), несколько интерфейсов (REST, Tkinter).
- Юнит-тесты с подменой репозиториев.
- Проще менять БД или UI, не ломая правила зависимостей.

## Поток данных (когда появится `core/`)

```
Запрос (HTTP или событие GUI) → адаптер → Use Case → Domain / Repository (интерфейс) → реализация SQLAlchemy → БД
```

## Технологии (зафиксированный стек обучения)

| Слой | Стек |
|------|------|
| Язык | **Python 3.13+** |
| ORM | **SQLAlchemy 2.0+** |
| Desktop | **Tkinter** |
| API (позже) | FastAPI, Pydantic, JWT — по mvp-guide |
| БД | SQLite на этапах A–C; PostgreSQL при деплое — по [MVP_TASK_PLAN.md](MVP_TASK_PLAN.md) |

## Порядок развития (кратко)

1. Сохранять **запускаемое** приложение как сейчас (фаза **A**).
2. Упорядочить монолит: модули, «репозитории без церемоний», pytest на логику (**B**).
3. Ввести `core/` и перенести use cases; Tkinter только вызывает их (**C**).
4. Добавить FastAPI (**D**), визуализацию дерева (**E**).

Подробнее: [MVP_TASK_PLAN.md](MVP_TASK_PLAN.md) §0.1–0.6, [ARCHITECTURE.md](ARCHITECTURE.md), [mvp-guide/README.md](mvp-guide/README.md).

## Документы

- `ARCHITECTURE.md` — слои и модули подробно.
- `PROJECT_STRUCTURE.md` — расширенный чертёж каталогов.
- `MVP_TASK_PLAN.md` — фазы, задачи MVP-*, календарь.
- `mvp-guide/` — пошаговые инструкции с примерами кода.
