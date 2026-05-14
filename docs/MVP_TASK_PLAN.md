# План задач MVP — Family Tree

> **Контекст:** Задачи рассчитаны на одного разработчика **без опыта в подобных проектах**, в режиме **обучения**: сначала сохранять и развивать **работающее приложение** (как в репозитории сейчас), затем **постепенно** выносить слои и подключать API, auth и визуализацию дерева — до полного объёма Clean Architecture.

> **Руководство по реализации:** пошаговые инструкции с примерами кода — в [docs/mvp-guide/](mvp-guide/README.md). Идентификаторы задач **MVP-*** ниже остаются опорными; **порядок выполнения** задайте по **фазам** (раздел 0.1), а не обязательно по номерам строк в старом календаре.

---

## 0.1 Фазы выполнения (рекомендуемый маршрут)

Принцип: **каждая фаза заканчивается запускаемым результатом**, который можно показать и отладить. «Большой» MVP из таблиц ниже — это **конечная цель**, а не обязанность сделать всё подряд до первого запуска.

| Фаза | Название | Что в руках после фазы | Что делать | Связь с задачами MVP-* |
|------|----------|------------------------|------------|-------------------------|
| **A** | **Baseline (уже есть)** | Рабочее десктоп-приложение на SQLite + Tkinter | Поддерживать `main.py` → `gui.py`, `models.py`, `database.py`, БД в `data/genealogy.db`. Исправления, мелкие фичи, при желании — разбиение `gui.py` на несколько модулей **без** обязательного `core/` | Вне формальной нумерации; параллельно **MVP-LEARN-02, 05, 06** |
| **B** | **Упорядоченный монолит** | Тот же стек (Python **3.13+**, SQLAlchemy **2.0+**, Tkinter), но код проще сопровождать | Вынести доступ к БД в отдельные функции/классы («репозитории без интерфейсов»), разнести UI по файлам (`views/`, `dialogs/`), добавить простые **pytest**-тесты на логику без GUI | Подготовка к MVP-INFRA без полной структуры `core/` |
| **C** | **Ядро + один клиент (Desktop)** | Каталог `core/` (domain → application → infrastructure), Tkinter только вызывает use cases | **MVP-INFRA-01–07**, **MVP-DOM-01–03**, **MVP-APP-*** по необходимости; сначала можно **один пользователь / без JWT**, потом добавить auth по плану | Строки таблиц §1.1–1.3 и выборочно 1.4 |
| **D** | **Второй клиент (FastAPI)** | Те же use cases с REST + Swagger | **MVP-INFRA-08**, **MVP-API-01–08**, тесты **MVP-TEST-*** | §1.4–1.5, §1.8 |
| **E** | **Визуализация дерева и полировка** | Web и/или Canvas в Tkinter, деплой по желанию | **MVP-WEB-01–04** и/или **MVP-DESK-08–13** | §1.6–1.7, итерации «полного» календаря §3 |

**Критический путь для обучения:** **A → B → C** (обязательно понять слои на рабочем GUI), затем **D** и **E** по интересу и времени.

---

## 0.11 Архитектура: принципы и что улучшено в плане

| Принцип | Зачем |
|--------|--------|
| **Вертикальный срез** | Вводить `core/` не слоем «весь domain», а цепочкой **один use case → один сценарий UI/API**, чтобы сразу проверять границы. |
| **SSOT схемы** | Поля БД и смысл связей — только в [mvp-guide/00-schema-and-mapping.md](mvp-guide/00-schema-and-mapping.md); остальные доки согласованы с ним. |
| **Реестр решений** | Нестандартные компромиссы (фазы, `owner_id`, транзакции, упаковка) — в [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md), чтобы не спорить с прошлым собой. |
| **`owner_id` до auth** | До JWT колонка может быть `NULL`; репозитории всё равно принимают `owner_id`/`user_id` в API, чтобы не ломать контракт при включении веба (см. ADR-004). |
| **Транзакции** | При нескольких операциях в одном сценарии — одна сессия и явная граница commit (см. ADR-006); не полагаться на «commit в каждом репозитории» для составных операций. |
| **Не смешивать async ORM в MVP** | Синхронные репозитории до стабильного API + нагрузочных измерений (ADR-005). |

**Нецели на фазе C (осознанно откладываем):** микросервисы, GraphQL, async SQLAlchemy, онлайн-обновление клиента, полная i18n.

---

## 0.2 Текущее состояние репозитория (факт)

Ниже — что **реально лежит в корне проекта** на момент актуализации документации. Целевая структура `core/`, `api/`, `desktop/` из [ARCHITECTURE.md](ARCHITECTURE.md) — это **следующие фазы**, а не текущий обязательный layout.

| Компонент | Путь | Статус |
|-----------|------|--------|
| Точка входа | `main.py` | Запускает Tkinter (`from gui import main`) |
| UI | `gui.py` | Список персон, диалоги, связи (`Relationship` ↔ `Person`) |
| ORM-модели | `models.py` | SQLAlchemy 2.0 style: `Person`, `Relationship`; связь второго лица — поле **`person_id_related`** |
| БД | `database.py`, `data/genealogy.db` | SQLite, `init_db()`, `SessionLocal` |
| Зависимости | `requirements.txt` | В т.ч. FastAPI и др. — **зарезервированы** на фазу D |
| Каталог `core/` | — | **Отсутствует** в репозитории; описан в документах и mvp-guide как цель фазы C |
| FastAPI-приложение | — | **Отсутствует** в репозитории; цель фазы D |

Документы `docs/mvp-guide/*.md` содержат примеры путей вида `core/...` и `desktop/...` — их нужно **создавать при миграции** или адаптировать пути под свою структуру на фазе B. **Схема полей БД** — [mvp-guide/00-schema-and-mapping.md](mvp-guide/00-schema-and-mapping.md); **зафиксированные архитектурные компромиссы** — [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md).

---

## 0.3 Архитектурные правила (обязательно при введении `core/`)

| Правило | Описание | Проверка |
|---------|----------|----------|
| **Dependency Rule** | Domain НЕ импортирует infrastructure. Application НЕ импортирует infrastructure напрямую — только через интерфейсы (`core/application/interfaces/`) | `grep -r "from core.infrastructure" core/domain/ core/application/` — 0 результатов (кроме DTO, которые могут ссылаться на domain enums) |
| **Единый Base** | `DeclarativeBase` объявлен **только** в `core/infrastructure/database/models/base.py`. Нигде больше не создаётся `declarative_base()` | Удалить `Base = declarative_base()` из `core/infrastructure/database/config.py` |
| **Синхронные репозитории для MVP** | Все репозитории — синхронные (`def`, не `async def`). FastAPI работает с sync через пул потоков. Async-репозитории — преждевременная оптимизация | Все методы `*Repository` — `def`, не `async def` |
| **owner_id фильтрация** | После включения multi-user все запросы к Person/Relationship фильтруются по `owner_id` текущего пользователя (JWT). `get_all()` / аналоги принимают `owner_id`. **До auth:** допустимы записи с `owner_id IS NULL` (десктоп); репозитории всё равно принимают параметр `owner_id` для единообразия с API | Нет публичного `get_all()` без параметра владельца после MVP-auth; в переходный период документировать правило для `NULL` |
| **UTC для дат** | `datetime.now(UTC)`, не `datetime.utcnow()` (удалён в Python 3.12+) | `grep -r "utcnow" core/` — 0 результатов |
| **Интерфейсы в application/** | `IPasswordService`, `ITokenService` находятся в `core/application/interfaces/`, адаптеры — в `core/infrastructure/auth/` | UseCase'ы зависят только от интерфейсов, не от конкретных реализаций |
| **Session lifecycle** | Сессия БД создаётся через `get_sync_session()` (generator), закрытие в `finally`. Репозитории НЕ управляют сессией | Нет `SyncSessionLocal()` вне `config.py`, сессия передаётся через DI |

---

## 0.4 Известные проблемы (чеклист при появлении `core/` и API)

Пути в таблице — **целевая структура** из mvp-guide; в текущем корне репозитория этих файлов **нет**. Исправлять по мере переноса кода с фазы **B** на **C**.

| ID | Проблема | Файл (после создания) | Исправление | Связанная задача |
|----|----------|----------------------|-------------|-------------------|
| BUG-01 | `Person.gender: Gender` — обязательное поле, но `CreatePersonDTO.gender = Field(None)` допускает `None`. `Person(gender=None)` → TypeError | `core/domain/entities/person.py` | Заменить `gender: Gender` на `gender: Gender \| None` | MVP-INFRA-02 |
| BUG-02 | `PersonRepository.get_by_id_and_owner_id` возвращает `Person`, а не `Person \| None`. При отсутствии записи — AttributeError вместо None | `core/domain/repositories/person_repository.py` | Изменить аннотацию на `-> Person \| None` | MVP-DOM-02 |
| BUG-03 | `PersonRepository.get_all()` не принимает `owner_id` — загружает ВСЕ персоны из БД | `core/domain/repositories/person_repository.py` | Добавить параметр `owner_id: int \| None = None` | MVP-INFRA-05 |
| BUG-04 | `CreateUserUseCase` напрямую импортирует `hash_password` из `core.infrastructure.auth.password_service` — нарушает Dependency Rule | `core/application/use_cases/user/create_user.py` | Использовать `IPasswordService` из `core/application/interfaces/` | MVP-APP-05-fix |
| BUG-05 | `core/infrastructure/database/config.py` создаёт свой `Base = declarative_base()` — дубликат, конфликтует с `models/base.py` | `core/infrastructure/database/config.py` | Удалить `Base`, импортировать из `models` | MVP-INFRA-07 |
| BUG-06 | `Settings` требует все PostgreSQL-поля без default — падает без `.env`. Нет поддержки SQLite | `core/infrastructure/config/settings.py` | Добавить `DB_TYPE`, defaults для SQLite | MVP-INFRA-07 |
| BUG-07 | `api/main.py` не имеет CORS, lifespan, exception handlers | `api/main.py` | Полная замена по MVP-API-01 | MVP-API-01 |
| BUG-08 | В таблице задач у `MVP-DESK-02` была ссылка на несуществующую `MVP-INFRA-10` | `MVP_TASK_PLAN.md` | Зависимость: `MVP-DESK-01`, `MVP-INFRA-04` (когда UserRepository готов) | MVP-DESK-02 |

**Legacy (корень репозитория, фаза A):** при расширении `models.py` / `gui.py` держать в уме те же идеи: одно имя поля связи **`person_id_related`** в ORM и в UI; `owner_id` в модели `Person` можно ввести заранее, но фильтрация по владельцу станет обязательной только с multi-user (фаза **C/D**).

---

## 0.5 Статус по фазам (актуализировать вручную по мере работы)

### Фаза A — сейчас в репозитории

| Компонент | Путь | Статус |
|-----------|------|--------|
| Запуск Tkinter + SQLite | `main.py`, `gui.py`, `database.py` | Работает |
| ORM | `models.py` | `Person`, `Relationship`; поле связи **`person_id_related`** |
| БД | `data/genealogy.db` | SQLite, `echo=True` в dev (при желании выключить) |

### Фазы C–E — создаётся по mvp-guide (пока нет в дереве файлов)

После появления `core/`, реализаций репозиториев, `api/`, `desktop/` (или вашего аналога) сверяйтесь с BUG-01–07 и таблицами §1.

**Типичный чеклист «с нуля»:** SQLAlchemy-модели в `core/infrastructure/database/models/`, реализации репозиториев, JWT и интерфейсы `IPasswordService` / `ITokenService`, роуты FastAPI, отдельные Tkinter-views, Alembic, корневой `conftest.py`, визуализация дерева (Web и/или Canvas).

---

## 0.6 Задачи на изучение (MVP-LEARN-*)

В [mvp-guide/README.md](mvp-guide/README.md) пошаговые **практические** инструкции не дублируют текст LEARN-задач — это нормально. Таблица ниже — **чеклист теории**; его можно проходить **параллельно фазам A–B**, а MVP-LEARN-03/04 отложить до старта фазы **D**.

| ID | Название | Слой | Сложность | Зависимости | Критерии приёмки |
|----|----------|------|-----------|-------------|-------------------|
| MVP-LEARN-01 | Изучение Clean Architecture: слои, зависимости, границы | — | M | — | Может нарисовать схему слоёв и объяснить, почему domain не зависит от infrastructure |
| MVP-LEARN-02 | Изучение SQLAlchemy 2.0: declarative models, sessions, relationships | — | L | — | Может создать модель с ForeignKey, выполнить CRUD через session |
| MVP-LEARN-03 | Изучение FastAPI: роутинг, Depends, Pydantic, Swagger | — | M | — | Может создать CRUD-эндпоинт с валидацией и автодокументацией |
| MVP-LEARN-04 | Изучение JWT-аутентификации: access/refresh, python-jose | — | M | — | Может вручную закодировать/декодировать JWT-токен |
| MVP-LEARN-05 | Изучение Tkinter: виджеты, layout, события, Canvas | — | M | — | Может создать окно с формой и кнопкой, обработать событие |
| MVP-LEARN-06 | Изучение pytest + unittest.mock: фикстуры, Mock, assert_called | — | M | — | Может написать тест с мок-репозиторием и проверить вызовы |
| MVP-LEARN-07 | Изучение алгоритмов графов: BFS/DFS для обхода дерева | — | M | — | Может написать функцию обхода графа персон по связям |

> **Итого на изучение: ~10 дней** (можно параллелить с практикой, но заложить время).

---

## 1. Список задач

Зависимости **MVP-LEARN-*** в колонке «Зависимости» — **рекомендация по теории** (см. §0.6), а не жёсткий gate: на фазах **A–B** можно заменить работой с текущим `gui.py` / `models.py`.

### 1.1 Инфраструктура и база данных

| ID | Название | Слой | Сложность | Зависимости | Требования | Критерии приёмки |
|----|----------|------|-----------|-------------|------------|-------------------|
| MVP-INFRA-01 | Настройка проекта: структура папок, pyproject.toml, requirements | Инфраструктура | M | MVP-LEARN-01 | — | Структура соответствует clean architecture, pytest запускается. Добавить `alembic`, `aiosqlite`, `email-validator`, `passlib` в зависимости. Создать корневой `conftest.py` |
| MVP-INFRA-02 | SQLAlchemy модели: User, Person, Relationship + связи между таблицами | Слой данных | L | MVP-INFRA-01, MVP-LEARN-02 | AUTH-05, PERS-06, PERS-07, REL-02 | Три модели с колонками, ForeignKey, методами to_domain()/from_domain(). **Включает исправление BUG-01** (Person.gender → Optional) и **BUG-05** (удалить дубликат Base из config.py) |
| MVP-INFRA-03 | Alembic: инициализация, начальная миграция | Слой данных | M | MVP-INFRA-02 | — | `alembic upgrade head` создаёт таблицы в SQLite |
| MVP-INFRA-04 | Реализация UserRepository (SQLAlchemy) | Слой данных | L | MVP-INFRA-02, MVP-DOM-01 | AUTH-01, AUTH-02, USER-01 | Все методы интерфейса работают с SQLite, покрыты тестами |
| MVP-INFRA-05 | Реализация PersonRepository (SQLAlchemy) | Слой данных | L | MVP-INFRA-02, MVP-DOM-02 | PERS-01–PERS-07 | CRUD + get_by_owner_id + get_by_id_and_owner_id работают |
| MVP-INFRA-06 | Реализация RelationshipRepository (SQLAlchemy) | Слой данных | L | MVP-INFRA-02, MVP-DOM-03 | REL-01–REL-07 | CRUD + get_by_person_id + get_by_type + проверка дубликатов |
| MVP-INFRA-07 | Конфигурация БД (SQLite dev, PostgreSQL prod) + settings.py | Инфраструктура | M | MVP-INFRA-03 | — | DATABASE_URL переключается по ENV, работает с обеими БД. **Включает исправление BUG-05** (удалить Base из config.py), **BUG-06** (Settings с defaults + SQLite). Обновить `api/dependencies/database.py` |

### 1.2 Domain-слой (entities, repositories, enums)

| ID | Название | Слой | Сложность | Зависимости | Требования | Критерии приёмки |
|----|----------|------|-----------|-------------|------------|-------------------|
| MVP-DOM-01 | Entity User + UserRepository интерфейс | Domain | S | MVP-INFRA-01 | AUTH-05, USER-01–USER-04 | Dataclass User с валидацией, ABC-репозиторий (пример в mvp-guide; перенос на фазу **C**) |
| MVP-DOM-02 | Entity Person + PersonRepository интерфейс | Domain | S | MVP-INFRA-01 | PERS-06, PERS-07 | Dataclass Person с owner_id, Gender enum, ABC-репозиторий. **Включает исправление BUG-01** (gender → Optional), **BUG-02** (get_by_id_and_owner_id → Optional), **BUG-03** (get_all с owner_id) |
| MVP-DOM-03 | Entity Relationship + RelationshipRepository интерфейс | Domain | S | MVP-INFRA-01 | REL-02, REL-06 | Dataclass Relationship, RelationshipType enum, ABC-репозиторий (пример в mvp-guide; перенос на фазу **C**) |

### 1.3 Application-слой (DTO, Use Cases)

| ID | Название | Слой | Сложность | Зависимости | Требования | Критерии приёмки |
|----|----------|------|-----------|-------------|------------|-------------------|
| MVP-APP-01 | DTO: CreateUserDTO, UpdateUserDTO, AdminUpdateUserDTO, ResponseUserDTO | Бизнес-логика | S | MVP-DOM-01 | AUTH-01, USER-02 | Реализуется в `core/` на фазе **C** (шаблон в mvp-guide) |
| MVP-APP-02 | DTO: CreatePersonDTO, UpdatePersonDTO, PersonResponseDTO | Бизнес-логика | S | MVP-DOM-02 | PERS-01, PERS-03, PERS-06 | Реализуется в `core/` на фазе **C** (шаблон в mvp-guide) |
| MVP-APP-03 | DTO: CreateRelationshipDTO, RelationshipResponseDTO | Бизнес-логика | M | MVP-DOM-03 | REL-01, REL-02 | RelationshipType enum в DTO, валидация person_1 ≠ person_2 |
| MVP-APP-04 | DTO: AuthDTO (LoginDTO, TokenResponseDTO, ForgotPasswordDTO, ResetPasswordDTO) | Бизнес-логика | M | MVP-DOM-01 | AUTH-02, AUTH-04, AUTH-06 | Все модели для auth-эндпоинтов |
| MVP-APP-05 | Use Case: CreateUserUseCase | Бизнес-логика | S | MVP-DOM-01, MVP-APP-01 | AUTH-01, AUTH-05 | При переносе из шаблона сразу заложить **MVP-APP-05-fix** (BUG-04: только `IPasswordService`) |
| MVP-APP-05-fix | Исправление CreateUserUseCase: внедрить IPasswordService вместо прямого импорта | Бизнес-логика | S | MVP-APP-06 (интерфейсы) | AUTH-05 | Создан `IPasswordService`, `CreateUserUseCase` зависит от интерфейса, не от infrastructure |
| MVP-APP-06 | Use Case: LoginUseCase | Бизнес-логика | M | MVP-DOM-01, MVP-INFRA-08 | AUTH-02, AUTH-05, AUTH-06 | Проверка пароля через bcrypt, генерация JWT-пары |
| MVP-APP-07 | Use Case: UpdateUserUseCase | Бизнес-логика | M | MVP-DOM-01, MVP-APP-01 | USER-02, USER-04 | Проверка уникальности email, username не меняется |
| MVP-APP-08 | Use Case: ChangePasswordUseCase | Бизнес-логика | M | MVP-DOM-01 | USER-03 | Проверка текущего пароля через verify_password, хеширование нового |
| MVP-APP-09 | Use Case: ForgotPasswordUseCase + ResetPasswordUseCase | Бизнес-логика | L | MVP-DOM-01, MVP-INFRA-09 | AUTH-04 | Генерация токена сброса с TTL, отправка email, сброс по токену |
| MVP-APP-10 | Use Case: CreatePersonUseCase | Бизнес-логика | S | MVP-DOM-02, MVP-APP-02 | PERS-01, PERS-07 | Реализуется в `core/` на фазе **C** (шаблон в mvp-guide) |
| MVP-APP-11 | Use Case: GetPersonUseCase + GetAllPersonsUseCase | Бизнес-логика | M | MVP-DOM-02 | PERS-02, PERS-05 | Проверка владения через owner_id, пагинация skip/limit |
| MVP-APP-12 | Use Case: UpdatePersonUseCase | Бизнес-логика | M | MVP-DOM-02, MVP-APP-02 | PERS-03 | Реализуется в `core/` на фазе **C** (шаблон в mvp-guide) |
| MVP-APP-13 | Use Case: DeletePersonUseCase | Бизнес-логика | L | MVP-DOM-02, MVP-DOM-03 | PERS-04 | Удаление персоны + каскадное удаление всех её связей в транзакции |
| MVP-APP-14 | Use Case: CreateRelationshipUseCase | Бизнес-логика | L | MVP-DOM-03, MVP-DOM-02 | REL-01, REL-06, REL-07 | Проверка владения обеими персонами, проверка дубликатов, валидация |
| MVP-APP-15 | Use Case: GetRelationshipsUseCase + GetRelationshipsByTypeUseCase | Бизнес-логика | M | MVP-DOM-03 | REL-04, REL-05 | Фильтрация по person_id и type |
| MVP-APP-16 | Use Case: DeleteRelationshipUseCase | Бизнес-логика | M | MVP-DOM-03 | REL-03 | Проверка владения перед удалением |
| MVP-APP-17 | Use Case: GetTreeDataUseCase | Бизнес-логика | L | MVP-DOM-02, MVP-DOM-03, MVP-LEARN-07 | TREE-01, TREE-06 | BFS-обход от корня, возвращает JSON {nodes, edges, generations} |

### 1.4 Инфраструктурные сервисы

| ID | Название | Слой | Сложность | Зависимости | Требования | Критерии приёмки |
|----|----------|------|-----------|-------------|------------|-------------------|
| MVP-INFRA-08 | JWT-сервис: генерация, валидация, refresh access/refresh токенов | Инфраструктура | L | MVP-INFRA-01, MVP-LEARN-04 | AUTH-06 | Access 15 мин, refresh 7 дней, python-jose, обработка истёкших токенов |
| MVP-INFRA-09 | Email-сервис: отправка писем (SMTP) + заглушка для dev | Инфраструктура | L | MVP-INFRA-01 | AUTH-04 | Письмо отправляется через SMTP, в dev — логирование в файл |

### 1.5 Presentation-слой (Web API)

| ID | Название | Слой | Сложность | Зависимости | Требования | Критерии приёмки |
|----|----------|------|-----------|-------------|------------|-------------------|
| MVP-API-01 | FastAPI app: роутер, middleware, CORS, exception handlers, lifespan | API | L | MVP-INFRA-01, MVP-LEARN-03 | — | Приложение запускается, Swagger доступен, CORS настроен |
| MVP-API-02 | Зависимость get_current_user (JWT-декодирование) + обработка ошибок | API | L | MVP-INFRA-08 | AUTH-06 | Извлекает user_id из токена, 401 если невалидный/истёкший |
| MVP-API-03 | Эндпоинты Auth: register, login, logout | API | L | MVP-APP-05, MVP-APP-06, MVP-API-02 | AUTH-01, AUTH-02, AUTH-03 | Регистрация 201, логин — токены, logout — инвалидация |
| MVP-API-04 | Эндпоинты Auth: forgot-password, reset-password | API | M | MVP-APP-09 | AUTH-04 | Письмо отправляется, пароль сбрасывается по токену |
| MVP-API-05 | Эндпоинты Users: GET/PUT /me, PUT /me/password | API | M | MVP-APP-07, MVP-APP-08, MVP-API-02 | USER-01–USER-03 | Профиль обновляется, пароль меняется |
| MVP-API-06 | Эндпоинты Persons: CRUD + список с пагинацией | API | L | MVP-APP-10–13, MVP-API-02 | PERS-01–PERS-05 | 5 эндпоинтов, owner_id из JWT, 403 при чужой персоне |
| MVP-API-07 | Эндпоинты Relationships: CRUD + фильтрация | API | L | MVP-APP-14–16, MVP-API-02 | REL-01–REL-05 | 4 эндпоинта, проверка владения, 400 при дубликате |
| MVP-API-08 | Эндпоинт Tree: GET /api/tree | API | L | MVP-APP-17, MVP-API-02 | TREE-01, TREE-06 | JSON-граф с nodes, edges, generations |

### 1.6 Визуализация дерева — Web

| ID | Название | Слой | Сложность | Зависимости | Требования | Критерии приёмки |
|----|----------|------|-----------|-------------|------------|-------------------|
| MVP-WEB-01 | HTML-страница-шаблон + подключение vis.js через CDN | Презентация | M | MVP-API-08 | TREE-01 | Страница загружается, vis.js подключен |
| MVP-WEB-02 | Рендеринг дерева: загрузка данных из API, создание графа vis.js | Презентация | XL | MVP-WEB-01, MVP-LEARN-07 | TREE-01, TREE-06 | Дерево отображается, навигация мышью (зум, перетаскивание) |
| MVP-WEB-03 | Клик по узлу → модальное окно с данными персоны (fetch из API) | Презентация | M | MVP-WEB-02, MVP-API-06 | TREE-03 | При клике показывается карточка с ФИО, датами, биографией |
| MVP-WEB-04 | Цветовое кодирование по полу и статусу жив/умер | Презентация | S | MVP-WEB-02 | TREE-04, TREE-05 | М — синий, Ж — розовый, Other — серый, умершие — пунктирная рамка |

### 1.7 Визуализация дерева — Desktop (Tkinter)

| ID | Название | Слой | Сложность | Зависимости | Требования | Критерии приёмки |
|----|----------|------|-----------|-------------|------------|-------------------|
| MVP-DESK-01 | Точка входа desktop: main.py, app.py, инициализация БД | Презентация | M | MVP-INFRA-07, MVP-LEARN-05 | — | Окно запускается, БД инициализируется, показывается экран входа |
| MVP-DESK-02 | Экран входа: форма email + пароль, кнопка «Войти» / «Регистрация» | Презентация | L | MVP-DESK-01, MVP-INFRA-04 | AUTH-02 | Вход проверяет пароль через verify_password, открывает главное окно |
| MVP-DESK-03 | Экран регистрации: форма username + email + пароль + подтверждение | Презентация | L | MVP-DESK-02, MVP-APP-05 | AUTH-01 | Регистрация через CreateUserUseCase, валидация, ошибки в messagebox |
| MVP-DESK-04 | Главное окно: меню, toolbar, таблица персон (Treeview) | Презентация | L | MVP-DESK-02, MVP-APP-11 | PERS-05 | Список персон в таблице, двойной клик → редактирование |
| MVP-DESK-05 | Форма персоны: создание/редактирование (все поля + Gender combobox) | Презентация | L | MVP-DESK-04, MVP-APP-10, MVP-APP-12 | PERS-01, PERS-03 | Форма с валидацией, сохранение через UseCase |
| MVP-DESK-06 | Удаление персоны: подтверждение + каскадное удаление связей | Презентация | M | MVP-DESK-04, MVP-APP-13 | PERS-04 | messagebox.askyesno, удаление через UseCase, обновление таблицы |
| MVP-DESK-07 | Панель связей: добавление/удаление связей для выбранной персоны | Презентация | L | MVP-DESK-04, MVP-APP-14, MVP-APP-16 | REL-01, REL-03 | Выбор второй персоны из списка, выбор типа связи, удаление связи |
| MVP-DESK-08 | Визуализация дерева на Canvas: отрисовка узлов и связей | Презентация | XL | MVP-DESK-04, MVP-APP-17, MVP-LEARN-05, MVP-LEARN-07 | TREE-01, TREE-06 | Узлы — прямоугольники с ФИО, связи — линии, раскладка по поколениям |
| MVP-DESK-09 | Навигация на Canvas: зум (колёсико), перетаскивание (drag) | Презентация | L | MVP-DESK-08 | TREE-02 | Зум +/-, перетаскивание холста мышью |
| MVP-DESK-10 | Клик по узлу → всплывающая карточка персоны | Презентация | M | MVP-DESK-08 | TREE-03 | Toplevel окно с данными персоны |
| MVP-DESK-11 | Цветовое кодирование узлов по полу + визуальное отличие умерших | Презентация | S | MVP-DESK-08 | TREE-04, TREE-05 | М — синий, Ж — розовый, умершие — серый фон/рамка |
| MVP-DESK-12 | Смена пароля: форма текущий → новый → подтверждение | Презентация | M | MVP-DESK-04, MVP-APP-08 | USER-03 | Проверка текущего пароля, сохранение нового |
| MVP-DESK-13 | Обработка ошибок: messagebox для ValueError, сетевых ошибок, сессий | Презентация | M | MVP-DESK-01 | — | Все исключения перехватываются, показывается понятное сообщение |

### 1.8 Тестирование

| ID | Название | Слой | Сложность | Зависимости | Требования | Критерии приёмки |
|----|----------|------|-----------|-------------|------------|-------------------|
| MVP-TEST-01 | Фикстуры и conftest.py | Тестирование | S | MVP-INFRA-01 | — | Добавить при появлении `tests/` и `core/` (фаза **C**) |
| MVP-TEST-02 | Unit-тесты: Auth use cases (CreateUser, Login, ChangePassword) | Тестирование | M | MVP-APP-05, MVP-APP-06, MVP-APP-08 | — | После реализации auth в `core/` (фаза **C/D**) |
| MVP-TEST-03 | Unit-тесты: Person use cases (CRUD) | Тестирование | M | MVP-APP-10–13 | — | >80% покрытие person use cases |
| MVP-TEST-04 | Unit-тесты: Relationship use cases | Тестирование | M | MVP-APP-14–16 | — | >80% покрытие relationship use cases |
| MVP-TEST-05 | Unit-тесты: DTO валидация (все DTO) | Тестирование | M | MVP-APP-01–04 | — | Невалидные данные → ValidationError |
| MVP-TEST-06 | Unit-тесты: GetTreeDataUseCase (обход графа) | Тестирование | M | MVP-APP-17 | — | Корректный обход дерева, циклы не ломают |
| MVP-TEST-07 | Integration-тесты: API Auth + Persons (httpx TestClient) | Тестирование | L | MVP-API-03, MVP-API-06 | — | Полный цикл: регистрация → вход → CRUD персон |
| MVP-TEST-08 | Integration-тесты: API Relationships + Tree (httpx TestClient) | Тестирование | L | MVP-API-07, MVP-API-08 | — | Создание связей → получение дерева |

---

## 2. Приоритеты MVP

### По фазам (согласовано с §0.1)

| Фаза | Минимальный результат | Задачи MVP-* (ориентир) |
|------|----------------------|-------------------------|
| **A** | Рабочий Tkinter + SQLite в корне | Нет обязательных ID; поддержка `main.py` / `gui.py` / `models.py` |
| **B** | Читаемый монолит + первые тесты | Параллельно MVP-LEARN-02, 05, 06; при желании Alembic из MVP-INFRA-03 |
| **C** | `core/` + Desktop на use cases | MVP-INFRA-01–07, MVP-DOM-01–03, MVP-APP-* для персон/связей (auth можно подключать последним блоком в C) |
| **D** | FastAPI поверх тех же use cases | MVP-INFRA-08, MVP-API-01–08, MVP-TEST-02–04, 06–08 |
| **E** | Дерево Web и/или Canvas | MVP-WEB-01–04, MVP-DESK-08–11 |

Ниже — **приоритеты «полного» multi-client MVP** (если идёте до конца по плану без сужения скоупа).

### Must have (полный multi-client MVP)
| ID задач | Количество |
|----------|-----------|
| MVP-INFRA-01–07, MVP-DOM-01–03, MVP-APP-01–03, MVP-APP-05-fix, MVP-APP-05–06, MVP-APP-10–17, MVP-INFRA-08, MVP-API-01–03, MVP-API-06–08, MVP-TEST-02–04, MVP-TEST-06 | **31** |

### Should have (желательно, можно отложить на неделю)
| ID задач | Количество |
|----------|-----------|
| MVP-APP-04, MVP-APP-07–09, MVP-INFRA-09, MVP-API-04–05, MVP-WEB-01–04, MVP-DESK-01–11, MVP-TEST-05, MVP-TEST-07–08 | **18** |

### Nice to have (бонус)
| ID задач | Количество |
|----------|-----------|
| MVP-DESK-12–13, MVP-TEST-01 | **3** |

---

## 3. Календарь итераций (полный объём плана)

Этот раздел — **примерный пошаговый календарь на ~16 недель**, если цель — сразу web + API + desktop с auth. При обучении через **фазы A→B→C** первые недели лучше потратить на **рабочий монолит** (§0.1), а строки ниже использовать как **справочник блоков**, а не жёсткие даты.

### Итерация 0: Изучение (10 дней, параллельно с практикой)

**Цель:** Разработчик разбирается в технологиях.

| День | Задачи |
|------|--------|
| 1–2 | MVP-LEARN-01 (Clean Architecture) + MVP-LEARN-02 (SQLAlchemy) |
| 3–4 | MVP-LEARN-03 (FastAPI) + MVP-LEARN-04 (JWT) |
| 5–6 | MVP-LEARN-05 (Tkinter) + MVP-LEARN-06 (pytest/mocks) |
| 7–8 | MVP-LEARN-07 (алгоритмы графов) — написать обход дерева на бумаге |
| 9–10 | Практика: мини-проект (FastAPI + SQLAlchemy CRUD одной сущности) |

---

### Итерация 1: Базовая инфраструктура + Auth (10 дней)

**Цель:** Пользователь может зарегистрироваться и войти через API.

| День | Задачи |
|------|--------|
| 1 | MVP-INFRA-01 (структура + зависимости), MVP-DOM-01 (User entity — ревью), **исправление BUG-01–03** (Person.gender, PersonRepository) |
| 2–3 | MVP-INFRA-02 (SQLAlchemy модели + **BUG-05** удалить Base из config), MVP-INFRA-03 (Alembic) |
| 4 | MVP-INFRA-04 (UserRepository), MVP-INFRA-07 (DB config + **BUG-06** Settings defaults) |
| 5 | MVP-INFRA-08 (JWT-сервис), MVP-APP-06 (LoginUseCase + интерфейсы IPasswordService/ITokenService) |
| 5.5 | **MVP-APP-05-fix** (исправление CreateUserUseCase → IPasswordService) |
| 6 | MVP-API-01 (FastAPI app + **BUG-07** CORS/lifespan), MVP-API-02 (get_current_user) |
| 7 | MVP-API-03 (Auth endpoints: register, login, logout) |
| 8 | MVP-APP-04 (Auth DTOs) |
| 9 | MVP-TEST-02 (Auth unit-тесты) |
| 10 | Багфикс, ревью, ручное тестирование через Swagger |

**Инкремент:** API регистрация + вход + JWT-токены + Swagger-документация.

---

### Итерация 2: Person CRUD (8 дней)

**Цель:** Пользователь может создавать и редактировать карточки персон через API.

| День | Задачи |
|------|--------|
| 1 | MVP-DOM-02, MVP-INFRA-05 (PersonRepository) |
| 2 | MVP-APP-11 (Get/GetAll), MVP-APP-13 (Delete) |
| 3 | MVP-API-06 (Person endpoints: все 5) |
| 4 | MVP-APP-03 (Relationship DTOs — подготовка) |
| 5 | MVP-TEST-03 (Person unit-тесты) |
| 6 | MVP-TEST-05 (DTO валидация — user + person) |
| 7–8 | Багфикс, ручное тестирование, рефакторинг |

**Инкремент:** Полный CRUD персон с изоляцией данных по owner_id.

---

### Итерация 3: Relationship CRUD + Tree API (10 дней)

**Цель:** Пользователь может создавать связи и получать данные дерева.

| День | Задачи |
|------|--------|
| 1 | MVP-DOM-03, MVP-INFRA-06 (RelationshipRepository) |
| 2 | MVP-APP-14 (CreateRelationshipUseCase — самая сложная: валидация) |
| 3 | MVP-APP-15 (GetRelationships), MVP-APP-16 (Delete) |
| 4 | MVP-API-07 (Relationship endpoints) |
| 5–6 | MVP-APP-17 (GetTreeDataUseCase — BFS-обход, формирование графа) |
| 7 | MVP-API-08 (Tree endpoint) |
| 8 | MVP-TEST-04 (Relationship unit-тесты) |
| 9 | MVP-TEST-06 (TreeData unit-тесты) |
| 10 | Багфикс, каскадное удаление, рефакторинг |

**Инкремент:** API для связей + данные дерева в JSON-формате.

---

### Итерация 4: Web-визуализация дерева (8 дней)

**Цель:** Пользователь видит своё дерево в браузере.

| День | Задачи |
|------|--------|
| 1 | MVP-WEB-01 (HTML-шаблон + vis.js CDN) |
| 2–4 | MVP-WEB-02 (Рендеринг: загрузка данных, создание графа, навигация) |
| 5 | MVP-WEB-03 (Клик по узлу → карточка) |
| 6 | MVP-WEB-04 (Цветовое кодирование) |
| 7 | MVP-TEST-07 (Integration-тесты Auth + Persons) |
| 8 | Багфикс, оптимизация, тесты на 100+ узлах |

**Инкремент:** Визуальное генеалогическое древо в браузере.

---

### Итерация 5: Desktop-клиент — базовый (10 дней)

**Цель:** Приложение запускается, можно войти и управлять персонами.

| День | Задачи |
|------|--------|
| 1 | MVP-DESK-01 (Точка входа, инициализация) |
| 2–3 | MVP-DESK-02 (Экран входа), MVP-DESK-03 (Регистрация) |
| 4–5 | MVP-DESK-04 (Главное окно + таблица персон) |
| 6–7 | MVP-DESK-05 (Форма персоны: создание/редактирование) |
| 8 | MVP-DESK-06 (Удаление персоны) |
| 9 | MVP-DESK-07 (Панель связей: добавление/удаление) |
| 10 | Багфикс, проверка всех сценариев |

**Инкремент:** Полноценный Desktop CRUD для персон и связей.

---

### Итерация 6: Desktop-визуализация дерева (8 дней)

**Цель:** Дерево отображается в Desktop-приложении.

| День | Задачи |
|------|--------|
| 1–3 | MVP-DESK-08 (Canvas: отрисовка узлов и связей, раскладка по поколениям) |
| 4–5 | MVP-DESK-09 (Навигация: зум, перетаскивание) |
| 6 | MVP-DESK-10 (Клик по узлу → карточка) |
| 7 | MVP-DESK-11 (Цветовое кодирование) |
| 8 | Багфикс, оптимизация производительности |

**Инкремент:** Визуальное дерево в Desktop-приложении.

---

### Итерация 7: User Management + Password Recovery (7 дней)

**Цель:** Полное управление профилем и восстановление пароля.

| День | Задачи |
|------|--------|
| 1 | MVP-APP-07 (UpdateUser), MVP-APP-08 (ChangePassword) |
| 2 | MVP-API-05 (User endpoints) |
| 3–4 | MVP-INFRA-09 (Email-сервис + заглушка для dev) |
| 5 | MVP-APP-09 (ForgotPassword + ResetPassword) |
| 6 | MVP-API-04 (Forgot/Reset endpoints) |
| 7 | MVP-DESK-12 (Смена пароля в Desktop) |

**Инкремент:** Полный цикл управления пользователем.

---

### Итерация 8: Полировка, тесты и деплой (8 дней)

**Цель:** MVP готов к релизу.

| День | Задачи |
|------|--------|
| 1 | MVP-TEST-07–08 (Integration-тесты) |
| 2 | MVP-DESK-13 (Обработка ошибок в Desktop) |
| 3 | Ревью кода, рефакторинг |
| 4 | Документация API (Swagger/OpenAPI описания) |
| 5 | Деплой Web: Docker + PostgreSQL + Nginx |
| 6 | Сборка Desktop: PyInstaller / .deb пакет |
| 7 | Smoke-тесты на проде + Desktop на чистой машине |
| 8 | Багфикс, финальный полировочный день |

**Инкремент:** Развёрнутый и работающий MVP (Web + Desktop).

---

## 4. Технические риски

| Риск | Связанные задачи | Вероятность | Влияние | Митигация |
|------|------------------|-------------|---------|-----------|
| **Сложность рендеринга дерева на Canvas (Tkinter)** | MVP-DESK-08, MVP-DESK-09 | Высокая | Высокое | Начать с простого: узлы — прямоугольники, связи — прямые линии. Подготовить fallback на Treeview (табличный вид). Ограничить глубину дерева 5 поколениями в первой версии |
| **Сложность рендеринга дерева в Web (vis.js)** | MVP-WEB-02 | Средняя | Высокое | vis.js Network — готовая библиотека, проще чем D3.js. Начать с минимальной конфигурации |
| **Каскадное удаление персоны со связями** | MVP-APP-13 | Средняя | Среднее | ON DELETE CASCADE в SQLAlchemy + явная транзакция. Написать тест на удаление персоны с 3+ связями |
| **Дублирование связей (A→B parent + B→A child)** | MVP-APP-14 | Средняя | Среднее | Хранить одну направленную связь. При отображении вычислять reverse_type. Написать тест на попытку создания дубликата |
| **Производительность дерева при 100+ персонах** | MVP-APP-17, MVP-DESK-08, MVP-WEB-02 | Средняя | Высокое | Ограничить глубину, ленивая подгрузка поколений. Тестировать на генерированных данных (100, 500, 1000 персон) |
| **JWT-Refresh: race conditions при одновременном обновлении** | MVP-INFRA-08 | Низкая | Среднее | Хранить refresh-токены в БД, инвалидировать по logout. Для MVP можно упростить — только access-токен |
| **Email-сервис не работает в dev-окружении** | MVP-INFRA-09 | Высокая | Низкое | Режим заглушки: логировать токен сброса в файл/консоль вместо отправки. В prod — реальный SMTP |
| **SQLite → PostgreSQL миграция** | MVP-INFRA-07 | Средняя | Среднее | SQLAlchemy абстракция + Alembic. Протестировать миграции на обеих БД до деплоя |
| **Tkinter Canvas: утечки памяти при перерисовке** | MVP-DESK-08 | Средняя | Среднее | Очищать Canvas перед перерисовкой (`delete('all')`), не накапливать объекты |
| **Неопытность: неправильная архитектура связей между слоями** | Все | Средняя | Высокое | Строгий запрет: domain НЕ импортирует infrastructure. Ревью на каждой итерации |
| **Шаблон use case при переносе в `core/`** | BUG-04, прямые импорты из infrastructure | Высокая | Высокое | Сразу вводить `IPasswordService`/`ITokenService` в `core/application/interfaces/`, адаптеры в `core/infrastructure/auth/` (см. MVP-APP-05-fix) |
| **Неопытность: непонимание SQLAlchemy session lifecycle** | MVP-INFRA-04–06 | Высокая | Высокое | Использовать контекстный менеджер для сессий. Написать integration-тесты с реальной БД |
| **Циклические связи в графе (A→B→C→A)** | MVP-APP-17 | Низкая | Высокое | BFS с visited-множеством. Обязательный тест на циклических данных |

---

## 5. Оценка трудоёмкости MVP

### По модулям

| Модуль | Задачи | Человеко-дни |
|--------|--------|--------------|
| **Изучение** | MVP-LEARN-01–07 | 10 |
| **Инфраструктура** | MVP-INFRA-01–09 | 10 |
| **Domain** | MVP-DOM-01–03 | 2 |
| **Application (DTO + Use Cases)** | MVP-APP-01–17 | 16 |
| **Web API** | MVP-API-01–08 | 12 |
| **Web-визуализация** | MVP-WEB-01–04 | 8 |
| **Desktop-клиент** | MVP-DESK-01–13 | 20 |
| **Тестирование** | MVP-TEST-01–08 | 12 |
| **Полировка + деплой** | — | 8 |
| **ИТОГО** | **51 задача** | **~98 человеко-дней** |

### По итерациям

| Итерация | Дней | Рабочих недель |
|----------|------|---------------|
| Итерация 0: Изучение | 10 | 2.0 |
| Итерация 1: Auth | 10 | 2.0 |
| Итерация 2: Person CRUD | 8 | 1.6 |
| Итерация 3: Relationship + Tree API | 10 | 2.0 |
| Итерация 4: Web-визуализация | 8 | 1.6 |
| Итерация 5: Desktop CRUD | 10 | 2.0 |
| Итерация 6: Desktop Tree | 8 | 1.6 |
| Итерация 7: User Management | 7 | 1.4 |
| Итерация 8: Полировка + деплой | 8 | 1.6 |
| **ИТОГО** | **79** | **~16 недель** |

> **С учётом непредвиденных задач (+30% буфер для неопытного разработчика): ~20 недель (5 месяцев)**

---

## 6. Резюме

| Метрика | Значение |
|---------|----------|
| **Всего задач в MVP** | 52 (+ 7 задач на изучение + 8 баг-фиксов = 67) |
| **Must have** | 31 |
| **Should have** | 18 |
| **Nice to have** | 3 |
| **Баг-фиксы в существующем коде** | 8 (BUG-01–08) |
| **Общая трудоёмкость** | ~100 человеко-дней |
| **С буфером 30% (неопытный разработчик)** | ~20 недель (5 месяцев) |
| **Количество итераций (полный календарь)** | 9 (раздел §3) |
| **Критический путь (обучение)** | **Фаза A → B → C** (рабочий GUI → монолит → `core/` + Tkinter) |
| **Критический путь (полный multi-client)** | Итерация 0 → 1 → 2 → 3 → 4/5 → 6 → 8 |
| **Наибольшие риски** | Desktop Canvas (MVP-DESK-08); session lifecycle SQLAlchemy |
| **Что уже есть в репозитории (фаза A)** | `main.py`, `gui.py`, `models.py`, `database.py`, SQLite в `data/` — рабочий прототип без `core/` |
| **Что появится на фазах C–E** | Каталог `core/`, FastAPI `api/`, разнесённый desktop, тесты по таблицам §1 |
| **Чеклист до переноса в `core/`** | BUG-01–07 по §0.4; в legacy — согласованность имён ORM (например `person_id_related`) |
| **Архитектурный реестр** | [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md) — ADR-lite, не дублировать в чатах |

---

## 7. Маппинг задач → файлы

Пути ниже соответствуют **целевой** структуре после фаз **C–D**. Пока код в корне (`gui.py`, `models.py`), используйте таблицу как **чеклист появляющихся файлов**, а не как описание текущего дерева.

### Инфраструктура

| Задача | Создать / обновить |
|--------|-------------------|
| MVP-INFRA-01 | `pyproject.toml`, `requirements/*.txt`, `conftest.py`, `core/__init__.py` |
| MVP-INFRA-02 | `core/infrastructure/database/models/base.py`, `user_model.py`, `person_model.py`, `relationship_model.py`, `__init__.py` |
| MVP-INFRA-03 | `alembic.ini`, `alembic/env.py`, `alembic/versions/` |
| MVP-INFRA-04 | `core/infrastructure/database/repositories/sqlalchemy_user_repository.py` |
| MVP-INFRA-05 | `core/infrastructure/database/repositories/sqlalchemy_person_repository.py` |
| MVP-INFRA-06 | `core/infrastructure/database/repositories/sqlalchemy_relationship_repository.py` |
| MVP-INFRA-07 | `core/infrastructure/config/settings.py`, `core/infrastructure/database/config.py`, `api/dependencies/database.py` |
| MVP-INFRA-08 | `core/infrastructure/auth/jwt_service.py` |
| MVP-INFRA-09 | `core/infrastructure/services/email_service.py`, `core/infrastructure/services/token_store.py` |

### Application

| Задача | Создать / обновить |
|--------|-------------------|
| MVP-APP-03 | `core/application/dto/relationship_dto.py` |
| MVP-APP-04 | `core/application/dto/auth_dto.py` |
| MVP-APP-05-fix | `core/application/interfaces/password_service.py`, `core/application/use_cases/user/create_user.py` |
| MVP-APP-06 | `core/application/interfaces/token_service.py`, `core/infrastructure/auth/password_service_adapter.py`, `core/infrastructure/auth/jwt_service_adapter.py`, `core/application/use_cases/user/login_user.py` |
| MVP-APP-08 | `core/application/use_cases/user/change_password.py` |
| MVP-APP-09 | `core/application/use_cases/user/forgot_password.py` |
| MVP-APP-11 | `core/application/use_cases/person/get_all_persons.py` |
| MVP-APP-13 | `core/application/use_cases/person/delete_person.py` |
| MVP-APP-14 | `core/application/use_cases/relationship/create_relationship.py` |
| MVP-APP-15 | `core/application/use_cases/relationship/get_relationships.py` |
| MVP-APP-16 | `core/application/use_cases/relationship/delete_relationship.py` |
| MVP-APP-17 | `core/application/use_cases/tree/get_tree_data.py` |

### API

| Задача | Создать / обновить |
|--------|-------------------|
| MVP-API-01 | `api/main.py` |
| MVP-API-02 | `api/dependencies/auth.py` |
| MVP-API-03 | `api/routes/auth.py` |
| MVP-API-04 | `api/routes/auth.py` (добавить forgot/reset) |
| MVP-API-05 | `api/routes/users.py` |
| MVP-API-06 | `api/routes/persons.py` |
| MVP-API-07 | `api/routes/relationships.py` |
| MVP-API-08 | `api/routes/tree.py` |

### Web-визуализация

| Задача | Создать / обновить |
|--------|-------------------|
| MVP-WEB-01 | `app/templates/tree.html` |
| MVP-WEB-02 | `app/static/tree.js` |
| MVP-WEB-03 | `app/static/tree.js` (добавить showPersonModal) |
| MVP-WEB-04 | `app/static/tree.js` (добавить цветовое кодирование) |

### Desktop

| Задача | Создать / обновить |
|--------|-------------------|
| MVP-DESK-01 | `desktop/main.py`, `desktop/app.py` |
| MVP-DESK-02 | `desktop/views/login_view.py` |
| MVP-DESK-03 | `desktop/views/register_view.py` |
| MVP-DESK-04 | `desktop/views/main_view.py` |
| MVP-DESK-05 | `desktop/views/person_form_view.py` |
| MVP-DESK-07 | `desktop/views/relationship_panel.py` |
| MVP-DESK-08 | `desktop/views/tree_canvas.py` |
| MVP-DESK-12 | `desktop/views/change_password_view.py` |
