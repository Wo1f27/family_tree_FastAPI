# 2. Domain-слой (entities, repositories, enums)

Схема полей и соглашения по связям — **[00-schema-and-mapping.md](00-schema-and-mapping.md)**. Примеры ORM/DTO/use case в остальных файлах mvp-guide приведены к этой схеме (`date_of_birth`, `person_id` / `person_id_related`, `owner_id` для будущего веба).

Целевые пути в блоках кода — `core/domain/...`. Пока каталога `core/` нет, создавайте файлы по мере фазы C.

---

### MVP-DOM-01 — Entity User + UserRepository интерфейс

**Шаблон:** `core/domain/entities/user.py`, `core/domain/repositories/user_repository.py` — когда подключаете регистрацию/логин (фаза D). До этого можно пропустить.

---

### MVP-DOM-02 — Entity Person + PersonRepository интерфейс

**Шаблон:** dataclass `Person` с полями как в **00-schema** (`date_of_birth`, `date_of_death`, `owner_id: int | None`, …) + ABC репозитория (`get_by_id`, `get_by_id_and_owner_id`, `list_by_owner`, `save`, `delete` — по вашему контракту).

---

### MVP-DOM-03 — Entity Relationship + RelationshipRepository интерфейс

**Шаблон:** доменная связь с `person_id`, `person_id_related`, `relationship_type: str` (или StrEnum со значениями `father` / `mother` / …). Без `start_date` / `end_date`, если не расширяете БД.

Интерфейс репозитория: `get_by_person_id` должен находить все рёбра, где `person_id == id OR person_id_related == id` (см. **00-schema**).
