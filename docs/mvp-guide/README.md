# Пошаговый MVP-гайд — Family Tree

## С чего начать

1. **[00-schema-and-mapping.md](00-schema-and-mapping.md)** — схема БД и домена под **текущий репозиторий** и задел под **пользователей / веб** (`owner_id`, позже `users`).
2. [MVP_TASK_PLAN.md](../MVP_TASK_PLAN.md) — фазы A→E и таблицы задач **MVP-***.
3. Ниже — файлы по слоям с примерами кода (ориентир на `core/`).

Практические шаги **MVP-LEARN-01–07** — чеклист в [MVP_TASK_PLAN.md](../MVP_TASK_PLAN.md) §0.6.

## Пути в примерах

Блоки `path=core/...`, `api/...`, `desktop/...` — **целевая** структура. Сейчас в корне может быть legacy (`gui.py`, `models.py`); перенос по фазам B–C.

## Структура документов

| Файл | Раздел |
|------|--------|
| [ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md) | ADR-lite: фазы, схема, транзакции, упаковка |
| [00-schema-and-mapping.md](00-schema-and-mapping.md) | Единая схема полей и смысл связей |
| [01-infrastructure.md](01-infrastructure.md) | MVP-INFRA-01 — MVP-INFRA-07 |
| [02-domain.md](02-domain.md) | MVP-DOM-01 — MVP-DOM-03 |
| [03-application.md](03-application.md) | MVP-APP-01 — MVP-APP-17 |
| [04-infra-services.md](04-infra-services.md) | MVP-INFRA-08 — MVP-INFRA-09 |
| [05-api.md](05-api.md) | MVP-API-01 — MVP-API-08 |
| [06-web.md](06-web.md) | MVP-WEB-01 — MVP-WEB-04 |
| [07-desktop.md](07-desktop.md) | MVP-DESK-01 — MVP-DESK-13 |

Стек: **Python 3.13+**, **SQLAlchemy 2.0+**, **Tkinter**; FastAPI — фаза D.

Оставшиеся расхождения с вашим локальным кодом (имена методов репозитория, наличие `User`) устраняйте при переносе; **имена колонок** держите как в **00-schema**.

Архитектурные компромиссы (фазы, транзакции, упаковка) — [ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md).
