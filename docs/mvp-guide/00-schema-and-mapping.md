# Схема данных и соглашения (репозиторий + будущий веб)

Этот файл — **единая точка правды** для примеров в `mvp-guide/*.md`. Они приведены к текущему корневому `models.py` и к плану **multi-user / веб** (`owner_id`, таблица `users` позже).

---

## Таблица `persons`

| Колонка | Тип | Примечание |
|---------|-----|--------------|
| `id` | PK | |
| `owner_id` | `INTEGER`, **NULL** | Сейчас в десктопе может быть `NULL`. После auth — `FK → users.id`, фильтрация списков по текущему пользователю. |
| `first_name`, `last_name` | `TEXT`/`VARCHAR` | Обязательны |
| `middle_name` | nullable | |
| `gender` | `VARCHAR` | Значения как в enum: `male` / `female` / `other` |
| `date_of_birth`, `date_of_death` | `DATE`, nullable | Именно **`date_of_*`**, не `date_birth`. |
| `biography` | `TEXT`, nullable | |
| `created_at`, `updated_at` | `DATETIME` | UTC |

**Доменная сущность** `Person` в `core/domain/entities/person.py` должна использовать **те же имена полей**, что и БД/ORM, чтобы `to_domain()` / `from_domain()` не путали.

Рекомендация по `gender`: в домене **`Gender | None`**, в DTO допускать отсутствие пола при создании — см. предупреждения в [01-infrastructure.md](01-infrastructure.md) (MVP-INFRA-02).

---

## Таблица `relationships`

Направленное ребро: **субъект** — `person_id`, **второй человек** — `person_id_related`, **`relationship_type`** — роль второго **по отношению к первому** (как в текущем `gui.py`).

| Колонка | Тип |
|---------|-----|
| `id` | PK |
| `person_id` | `FK → persons.id` |
| `person_id_related` | `FK → persons.id` |
| `relationship_type` | `VARCHAR` |

Примеры значений `relationship_type` (строки): `father`, `mother`, `child`, `spouse`, `sibling`.

Смысл:

- `person_id=A`, `person_id_related=B`, `father` → у **A** отец **B**.
- `person_id=P`, `person_id_related=C`, `child` → у **P** ребёнок **C**.

Отдельных колонок `start_date` / `end_date` у связи **нет** (при появлении событий — отдельная таблица позже).

---

## Репозиторий связей: участие персоны

«Все связи, где участвует `P`»:

```text
person_id = P  OR  person_id_related = P
```

Дубликаты и обратные роли (father ↔ child) — на уровне use case / сервиса, по правилам вашего приложения (как в `gui.py`: `_has_equivalent_relationship`).

---

## Веб и владение

- **Сейчас (десктоп):** можно не фильтровать по `owner_id` или считать `owner_id IS NULL` «общими» записями — на усмотрение первого релиза.
- **Потом (API):** все выборки персон и связей — только при совпадении `owner_id` с `user_id` из JWT (или через `get_by_id_and_owner_id`).

Примеры use case в гайде с параметром `user_id: int` рассчитаны на **этот** переход.

---

## Имена в коде примеров

| Было в старых черновиках гайда | Сейчас в примерах |
|-------------------------------|-------------------|
| `person_1`, `person_2` | `person_id`, `person_id_related` |
| `date_birth`, `date_death` | `date_of_birth`, `date_of_death` |
| `related_person_id` | не использовать |

Таблица **`users`** и модель **`UserModel`** в примерах MVP-INFRA-02 остаются для фазы с регистрацией/логином; до её реализации `owner_id` остаётся без FK или с nullable FK — как решите в первой миграции Alembic.

---

## Транзакции

- Одна **SQLAlchemy Session** на действие в GUI или на HTTP-запрос при нескольких изменениях в БД.
- **Коммит** на границе сценария (use case / dependency), а не «по коммиту в каждом методе репозитория», если нужна атомарность нескольких шагов — см. [ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md) (ADR-006).
