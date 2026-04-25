# План задач MVP — Family Tree

> **Контекст:** Задачи рассчитаны на одного бэкенд-разработчика **без опыта в подобных проектах**. Сложности увеличены относительно «опытной» оценки, добавлены задачи на изучение технологий. Desktop-визуализация включена как полноценный клиент MVP.

> **Руководство по реализации:** Детальные инструкции с кодом для каждой задачи — в [docs/mvp-guide/](docs/mvp-guide/README.md).

---

## 0. Архитектурные правила (обязательно для соблюдения)

| Правило | Описание | Проверка |
|---------|----------|----------|
| **Dependency Rule** | Domain НЕ импортирует infrastructure. Application НЕ импортирует infrastructure напрямую — только через интерфейсы (`core/application/interfaces/`) | `grep -r "from core.infrastructure" core/domain/ core/application/` — 0 результатов (кроме DTO, которые могут ссылаться на domain enums) |
| **Единый Base** | `DeclarativeBase` объявлен **только** в `core/infrastructure/database/models/base.py`. Нигде больше не создаётся `declarative_base()` | Удалить `Base = declarative_base()` из `core/infrastructure/database/config.py` |
| **Синхронные репозитории для MVP** | Все репозитории — синхронные (`def`, не `async def`). FastAPI работает с sync через пул потоков. Async-репозитории — преждевременная оптимизация | Все методы `*Repository` — `def`, не `async def` |
| **owner_id фильтрация** | Все запросы к Person/Relationship фильтруются по `owner_id` текущего пользователя. `get_all()` принимает `owner_id` | Нет метода `get_all()` без `owner_id` для персон |
| **UTC для дат** | `datetime.now(UTC)`, не `datetime.utcnow()` (удалён в Python 3.12+) | `grep -r "utcnow" core/` — 0 результатов |
| **Интерфейсы в application/** | `IPasswordService`, `ITokenService` находятся в `core/application/interfaces/`, адаптеры — в `core/infrastructure/auth/` | UseCase'ы зависят только от интерфейсов, не от конкретных реализаций |
| **Session lifecycle** | Сессия БД создаётся через `get_sync_session()` (generator), закрытие в `finally`. Репозитории НЕ управляют сессией | Нет `SyncSessionLocal()` вне `config.py`, сессия передаётся через DI |

---

## 0.1 Известные проблемы в существующем коде (исправить до/во время итерации 1)

| ID | Проблема | Файл | Исправление | Связанная задача |
|----|----------|------|-------------|-------------------|
| BUG-01 | `Person.gender: Gender` — обязательное поле, но `CreatePersonDTO.gender = Field(None)` допускает `None`. `Person(gender=None)` → TypeError | `core/domain/entities/person.py` | Заменить `gender: Gender` на `gender: Gender \| None` | MVP-INFRA-02 |
| BUG-02 | `PersonRepository.get_by_id_and_owner_id` возвращает `Person`, а не `Person \| None`. При отсутствии записи — AttributeError вместо None | `core/domain/repositories/person_repository.py` | Изменить аннотацию на `-> Person \| None` | MVP-DOM-02 |
| BUG-03 | `PersonRepository.get_all()` не принимает `owner_id` — загружает ВСЕ персоны из БД | `core/domain/repositories/person_repository.py` | Добавить параметр `owner_id: int \| None = None` | MVP-INFRA-05 |
| BUG-04 | `CreateUserUseCase` напрямую импортирует `hash_password` из `core.infrastructure.auth.password_service` — нарушает Dependency Rule | `core/application/use_cases/user/create_user.py` | Использовать `IPasswordService` из `core/application/interfaces/` | MVP-APP-05-fix |
| BUG-05 | `core/infrastructure/database/config.py` создаёт свой `Base = declarative_base()` — дубликат, конфликтует с `models/base.py` | `core/infrastructure/database/config.py` | Удалить `Base`, импортировать из `models` | MVP-INFRA-07 |
| BUG-06 | `Settings` требует все PostgreSQL-поля без default — падает без `.env`. Нет поддержки SQLite | `core/infrastructure/config/settings.py` | Добавить `DB_TYPE`, defaults для SQLite | MVP-INFRA-07 |
| BUG-07 | `api/main.py` не имеет CORS, lifespan, exception handlers | `api/main.py` | Полная замена по MVP-API-01 | MVP-API-01 |
| BUG-08 | `MVP-DESK-02` зависит от `MVP-INFRA-10` — такой задачи не существует | данный файл | Убрать зависимость, заменить на `MVP-INFRA-04` | MVP-DESK-02 |

---

## 0.2 Статус реализации (что реально сделано)

| Компонент | Файл | Статус | Комментарий |
|-----------|------|--------|-------------|
| Entity User | `core/domain/entities/user.py` | ✅ Готово | Dataclass с валидацией |
| Entity Person | `core/domain/entities/person.py` | ⚠️ Баг BUG-01 | `gender` не Optional |
| Entity Relationship | `core/domain/entities/relationship.py` | ✅ Готово | С `get_reverse_type()` |
| UserRepository interface | `core/domain/repositories/user_repository.py` | ✅ Готово | ABC с 7 методами |
| PersonRepository interface | `core/domain/repositories/person_repository.py` | ⚠️ Баг BUG-02, BUG-03 | Возврат тип, нет owner_id |
| RelationshipRepository interface | `core/domain/repositories/relationship_repository.py` | ✅ Готово | ABC с 7 методами |
| CreateUserDTO | `core/application/dto/user_dto.py` | ✅ Готово | 4 DTO |
| CreatePersonDTO | `core/application/dto/person_dto.py` | ⚠️ gender=None при Gender обязательном | 3 DTO |
| CreateUserUseCase | `core/application/use_cases/user/create_user.py` | ⚠️ Баг BUG-04 | Нарушает Dependency Rule |
| UpdateUserUseCase | `core/application/use_cases/user/update_user.py` | ✅ Готово | |
| GetPersonUseCase | `core/application/use_cases/person/get_person.py` | ✅ Готово | |
| CreatePersonUseCase | `core/application/use_cases/person/create_person.py` | ✅ Готово | |
| UpdatePersonUseCase | `core/application/use_cases/person/update_person.py` | ✅ Готово | |
| Password service | `core/infrastructure/auth/password_service.py` | ✅ Готово | bcrypt |
| DB config | `core/infrastructure/database/config.py` | ⚠️ Баг BUG-05, BUG-06 | Только PostgreSQL, дубликат Base |
| Settings | `core/infrastructure/config/settings.py` | ⚠️ Баг BUG-06 | Нет SQLite, нет defaults |
| API main | `api/main.py` | ⚠️ Баг BUG-07 | Нет CORS/lifespan |
| Test fixtures | `tests/fixtures/fixtures.py` | ✅ Готово | mock_user_repo, mock_person_repo |
| Test CreateUser | `tests/unit/use_cases/test_create_user.py` | ✅ Готово | 3 теста |
| Test UpdateUser | `tests/unit/use_cases/test_update_user.py` | ✅ Готово | |
| Test CreatePerson | `tests/unit/use_cases/test_create_person.py` | ✅ Готово | |
| Test UpdatePerson | `tests/unit/use_cases/test_update_person.py` | ✅ Готово | |

**Не существует (нужно создать с нуля):**
- SQLAlchemy модели (`models/base.py`, `user_model.py`, `person_model.py`, `relationship_model.py`)
- Все repository реализации (`sqlalchemy_*_repository.py`)
- JWT-сервис (`jwt_service.py`) + адаптеры
- Email-сервис (`email_service.py`, `token_store.py`)
- Application интерфейсы (`IPasswordService`, `ITokenService`)
- Auth DTO (`auth_dto.py`, `relationship_dto.py`)
- Все API роуты (`auth.py`, `users.py`, `persons.py`, `relationships.py`, `tree.py`)
- API зависимость `get_current_user`
- Все Desktop views (`login_view.py`, `main_view.py`, `tree_canvas.py`, …)
- Web шаблоны (`tree.html`, `tree.js`)
- Alembic конфигурация
- Корневой `conftest.py`

---

## 0.3 Задачи на изучение (перед стартом итераций)

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

### 1.1 Инфраструктура и база данных

| ID | Название | Слой | Сложность | Зависимости | Требования | Критерии приёмки |
|----|----------|------|-----------|-------------|------------|-------------------|
| MVP-INFRA-01 | Настройка проекта: структура папок, pyproject.toml, requirements | Инфраструктура | M | MVP-LEARN-01 | — | Структура соответствует clean architecture, pytest запускается. Добавить `alembic`, `aiosqlite`, `email-validator`, `passlib` в зависимости. Создать корневой `conftest.py` |
| MVP-INFRA-02 | SQLAlchemy модели: User, Person, Relationship + связи между таблицами | Слой данных | L | MVP-INFRA-02, MVP-LEARN-02 | AUTH-05, PERS-06, PERS-07, REL-02 | Три модели с колонками, ForeignKey, методами to_domain()/from_domain(). **Включает исправление BUG-01** (Person.gender → Optional) и **BUG-05** (удалить дубликат Base из config.py) |
| MVP-INFRA-03 | Alembic: инициализация, начальная миграция | Слой данных | M | MVP-INFRA-02 | — | `alembic upgrade head` создаёт таблицы в SQLite |
| MVP-INFRA-04 | Реализация UserRepository (SQLAlchemy) | Слой данных | L | MVP-INFRA-02, MVP-DOM-01 | AUTH-01, AUTH-02, USER-01 | Все методы интерфейса работают с SQLite, покрыты тестами |
| MVP-INFRA-05 | Реализация PersonRepository (SQLAlchemy) | Слой данных | L | MVP-INFRA-02, MVP-DOM-02 | PERS-01–PERS-07 | CRUD + get_by_owner_id + get_by_id_and_owner_id работают |
| MVP-INFRA-06 | Реализация RelationshipRepository (SQLAlchemy) | Слой данных | L | MVP-INFRA-02, MVP-DOM-03 | REL-01–REL-07 | CRUD + get_by_person_id + get_by_type + проверка дубликатов |
| MVP-INFRA-07 | Конфигурация БД (SQLite dev, PostgreSQL prod) + settings.py | Инфраструктура | M | MVP-INFRA-03 | — | DATABASE_URL переключается по ENV, работает с обеими БД. **Включает исправление BUG-05** (удалить Base из config.py), **BUG-06** (Settings с defaults + SQLite). Обновить `api/dependencies/database.py` |

### 1.2 Domain-слой (entities, repositories, enums)

| ID | Название | Слой | Сложность | Зависимости | Требования | Критерии приёмки |
|----|----------|------|-----------|-------------|------------|-------------------|
| MVP-DOM-01 | Entity User + UserRepository интерфейс | Domain | S | MVP-INFRA-01 | AUTH-05, USER-01–USER-04 | Dataclass User с валидацией, ABC-репозиторий ✅ (частично готово) |
| MVP-DOM-02 | Entity Person + PersonRepository интерфейс | Domain | S | MVP-INFRA-01 | PERS-06, PERS-07 | Dataclass Person с owner_id, Gender enum, ABC-репозиторий. **Включает исправление BUG-01** (gender → Optional), **BUG-02** (get_by_id_and_owner_id → Optional), **BUG-03** (get_all с owner_id) |
| MVP-DOM-03 | Entity Relationship + RelationshipRepository интерфейс | Domain | S | MVP-INFRA-01 | REL-02, REL-06 | Dataclass Relationship, RelationshipType enum, ABC-репозиторий ✅ (частично готово) |

### 1.3 Application-слой (DTO, Use Cases)

| ID | Название | Слой | Сложность | Зависимости | Требования | Критерии приёмки |
|----|----------|------|-----------|-------------|------------|-------------------|
| MVP-APP-01 | DTO: CreateUserDTO, UpdateUserDTO, AdminUpdateUserDTO, ResponseUserDTO | Бизнес-логика | S | MVP-DOM-01 | AUTH-01, USER-02 | ✅ Уже реализовано |
| MVP-APP-02 | DTO: CreatePersonDTO, UpdatePersonDTO, PersonResponseDTO | Бизнес-логика | S | MVP-DOM-02 | PERS-01, PERS-03, PERS-06 | ✅ Уже реализовано |
| MVP-APP-03 | DTO: CreateRelationshipDTO, RelationshipResponseDTO | Бизнес-логика | M | MVP-DOM-03 | REL-01, REL-02 | RelationshipType enum в DTO, валидация person_1 ≠ person_2 |
| MVP-APP-04 | DTO: AuthDTO (LoginDTO, TokenResponseDTO, ForgotPasswordDTO, ResetPasswordDTO) | Бизнес-логика | M | MVP-DOM-01 | AUTH-02, AUTH-04, AUTH-06 | Все модели для auth-эндпоинтов |
| MVP-APP-05 | Use Case: CreateUserUseCase | Бизнес-логика | S | MVP-DOM-01, MVP-APP-01 | AUTH-01, AUTH-05 | ⚠️ Реализовано, но нарушает Dependency Rule (BUG-04) |
| MVP-APP-05-fix | Исправление CreateUserUseCase: внедрить IPasswordService вместо прямого импорта | Бизнес-логика | S | MVP-APP-06 (интерфейсы) | AUTH-05 | Создан `IPasswordService`, `CreateUserUseCase` зависит от интерфейса, не от infrastructure |
| MVP-APP-06 | Use Case: LoginUseCase | Бизнес-логика | M | MVP-DOM-01, MVP-INFRA-08 | AUTH-02, AUTH-05, AUTH-06 | Проверка пароля через bcrypt, генерация JWT-пары |
| MVP-APP-07 | Use Case: UpdateUserUseCase | Бизнес-логика | M | MVP-DOM-01, MVP-APP-01 | USER-02, USER-04 | Проверка уникальности email, username не меняется |
| MVP-APP-08 | Use Case: ChangePasswordUseCase | Бизнес-логика | M | MVP-DOM-01 | USER-03 | Проверка текущего пароля через verify_password, хеширование нового |
| MVP-APP-09 | Use Case: ForgotPasswordUseCase + ResetPasswordUseCase | Бизнес-логика | L | MVP-DOM-01, MVP-INFRA-09 | AUTH-04 | Генерация токена сброса с TTL, отправка email, сброс по токену |
| MVP-APP-10 | Use Case: CreatePersonUseCase | Бизнес-логика | S | MVP-DOM-02, MVP-APP-02 | PERS-01, PERS-07 | ✅ Уже реализовано |
| MVP-APP-11 | Use Case: GetPersonUseCase + GetAllPersonsUseCase | Бизнес-логика | M | MVP-DOM-02 | PERS-02, PERS-05 | Проверка владения через owner_id, пагинация skip/limit |
| MVP-APP-12 | Use Case: UpdatePersonUseCase | Бизнес-логика | M | MVP-DOM-02, MVP-APP-02 | PERS-03 | ✅ Уже реализовано |
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
| MVP-TEST-01 | Фикстуры и conftest.py | Тестирование | S | MVP-INFRA-01 | — | ✅ Уже реализовано |
| MVP-TEST-02 | Unit-тесты: Auth use cases (CreateUser, Login, ChangePassword) | Тестирование | M | MVP-APP-05, MVP-APP-06, MVP-APP-08 | — | ✅ Частично реализовано, доработать Login |
| MVP-TEST-03 | Unit-тесты: Person use cases (CRUD) | Тестирование | M | MVP-APP-10–13 | — | >80% покрытие person use cases |
| MVP-TEST-04 | Unit-тесты: Relationship use cases | Тестирование | M | MVP-APP-14–16 | — | >80% покрытие relationship use cases |
| MVP-TEST-05 | Unit-тесты: DTO валидация (все DTO) | Тестирование | M | MVP-APP-01–04 | — | Невалидные данные → ValidationError |
| MVP-TEST-06 | Unit-тесты: GetTreeDataUseCase (обход графа) | Тестирование | M | MVP-APP-17 | — | Корректный обход дерева, циклы не ломают |
| MVP-TEST-07 | Integration-тесты: API Auth + Persons (httpx TestClient) | Тестирование | L | MVP-API-03, MVP-API-06 | — | Полный цикл: регистрация → вход → CRUD персон |
| MVP-TEST-08 | Integration-тесты: API Relationships + Tree (httpx TestClient) | Тестирование | L | MVP-API-07, MVP-API-08 | — | Создание связей → получение дерева |

---

## 2. Приоритеты MVP

### Must have (обязательно для запуска)
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

## 3. Итерации внутри MVP

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
| **Существующий код нарушает Dependency Rule** | BUG-04 (CreateUserUseCase), все UseCase'ы | Высокая | Высокое | Создать `IPasswordService`/`ITokenService` в `core/application/interfaces/`, адаптеры в `core/infrastructure/auth/`. Исправить все UseCase'ы до начала новых задач |
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
| **Количество итераций** | 9 (0–8) |
| **Критический путь** | Итерация 0 → 1 → 2 → 3 → 4/5 → 6 → 8 |
| **Наибольшие риски** | Desktop-визуализация на Canvas (MVP-DESK-08) — XL сложность; SQLAlchemy session lifecycle для неопытного разработчика |
| **Что уже сделано** | Entities, DTO, password service, фикстуры, часть тестов — экономит ~5 дней |
| **Что требует исправления** | 8 багов (BUG-01–08), исправляются в итерации 1 |

---

## 7. Маппинг задач → файлы

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
