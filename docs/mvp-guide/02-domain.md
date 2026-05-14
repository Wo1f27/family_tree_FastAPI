# 2. Domain-слой (entities, repositories, enums)

---

### MVP-DOM-01 — Entity User + UserRepository интерфейс

**Статус: ✅ Уже реализовано.** Файлы `core/domain/entities/user.py` и `core/domain/repositories/user_repository.py` существуют и соответствуют требованиям.

---

### MVP-DOM-02 — Entity Person + PersonRepository интерфейс

**Статус: ✅ Уже реализовано.** Файлы `core/domain/entities/person.py` (с `Gender` enum, `owner_id`) и `core/domain/repositories/person_repository.py` (с `get_by_id_and_owner_id`) существуют.

---

### MVP-DOM-03 — Entity Relationship + RelationshipRepository интерфейс

**Статус: ✅ Уже реализовано.** Файлы `core/domain/entities/relationship.py` (с `RelationshipType` enum) и `core/domain/repositories/relationship_repository.py` существуют.
