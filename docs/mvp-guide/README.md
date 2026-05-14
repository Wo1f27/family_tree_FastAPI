# Пошаговый MVP-гайд — Family Tree

## Как читать этот каталог

1. **Сначала** откройте [MVP_TASK_PLAN.md](../MVP_TASK_PLAN.md) — там **фазы A→E** (от текущего рабочего приложения к `core/` и FastAPI) и таблицы задач **MVP-***.
2. **Затем** выберите файл по слою — внутри пошаговые инструкции и примеры кода.

Практические шаги **MVP-LEARN-01–07** в эти файлы **не вынесены** (это чеклист теории в [MVP_TASK_PLAN.md](../MVP_TASK_PLAN.md) §0.6). Зависимости вида `MVP-LEARN-*` в таблицах §1 означают: «иметь базовое понимание темы»; их можно проходить **параллельно фазам A–B**, а FastAPI/JWT (LEARN-03/04) — ближе к фазе **D**.

## Пути в примерах кода

Файлы вроде `core/...`, `desktop/...`, `api/...` в блоках кода — **целевая структура**. В корне репозитория сейчас лежит **legacy** (`gui.py`, `models.py` и т.д.); при фазе **B** можно переносить код в новые папки, при фазе **C** — совмещать с layout из гайда.

**Имя поля связи в ORM:** в учебном коде и в текущем `models.py` используйте одно имя — **`person_id_related`** (второй человек в связи); не смешивать с устаревшим `related_person_id` из черновиков.

## Структура документов

| Файл | Раздел | Задачи |
|------|--------|--------|
| [01-infrastructure.md](01-infrastructure.md) | Инфраструктура и база данных | MVP-INFRA-01 — MVP-INFRA-07 |
| [02-domain.md](02-domain.md) | Domain-слой | MVP-DOM-01 — MVP-DOM-03 |
| [03-application.md](03-application.md) | Application-слой (DTO, Use Cases) | MVP-APP-01 — MVP-APP-17 |
| [04-infra-services.md](04-infra-services.md) | Инфраструктурные сервисы | MVP-INFRA-08 — MVP-INFRA-09 |
| [05-api.md](05-api.md) | Presentation-слой (Web API) | MVP-API-01 — MVP-API-08 |
| [06-web.md](06-web.md) | Визуализация дерева — Web | MVP-WEB-01 — MVP-WEB-04 |
| [07-desktop.md](07-desktop.md) | Desktop (Tkinter): вход, CRUD, Canvas | MVP-DESK-01 — MVP-DESK-13 |

Стек обучения: **Python 3.13+**, **SQLAlchemy 2.0+**, **Tkinter**; FastAPI — по мере фазы **D**.
