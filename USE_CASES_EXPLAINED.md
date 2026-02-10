# Что такое Use Cases?

## 🎯 Простое объяснение

**Use Case (Сценарий использования)** — это **бизнес-операция**, которую может выполнить пользователь в вашем приложении.

Это как **рецепт приготовления блюда**:
- **Ингредиенты** (DTO) → **Действия** (Use Case) → **Результат** (Entity)

## 📝 Примеры из вашего проекта

### Пример 1: Создание пользователя

**Use Case:** `CreateUserUseCase`

**Что делает:**
1. Принимает данные нового пользователя (DTO)
2. Проверяет, что такого пользователя еще нет
3. Хеширует пароль
4. Создает пользователя в базе данных
5. Возвращает созданного пользователя

**Где используется:**
- ✅ В API: когда пользователь регистрируется через веб-форму
- ✅ В Desktop: когда администратор создает пользователя
- ✅ В Mobile: когда пользователь регистрируется в приложении

**Одна логика → три интерфейса!**

### Пример 2: Получение генеалогического дерева

**Use Case:** `GetFamilyTreeUseCase`

**Что делает:**
1. Принимает ID персоны
2. Находит всех родственников (родители, дети, супруги)
3. Строит дерево связей
4. Возвращает структурированное дерево

**Где используется:**
- ✅ В API: `/api/persons/123/tree`
- ✅ В Desktop: отображение дерева в окне
- ✅ В Mobile: показ дерева на экране

## 🏗 Архитектура Use Case

```
┌─────────────────────────────────────┐
│   Presentation Layer                │
│   (API Route / Desktop UI)          │
└──────────────┬──────────────────────┘
               │ вызывает
               ▼
┌─────────────────────────────────────┐
│   Use Case                          │
│   - Валидация                       │
│   - Бизнес-правила                  │
│   - Координация                     │
└──────────────┬──────────────────────┘
               │ использует
               ▼
┌─────────────────────────────────────┐
│   Repository                        │
│   (Работа с БД)                     │
└─────────────────────────────────────┘
```

## 💻 Пример кода

### Use Case для создания персоны

```python
# core/application/use_cases/person/create_person.py

from core.domain.entities.person import Person
from core.domain.repositories.person_repository import IPersonRepository
from core.application.dto.person_dto import CreatePersonDTO


class CreatePersonUseCase:
    """
    Use Case для создания персоны в генеалогическом дереве.
    
    Это бизнес-операция, которая:
    1. Валидирует данные
    2. Применяет бизнес-правила
    3. Создает персону через репозиторий
    """
    
    def __init__(self, person_repository: IPersonRepository):
        """
        Инициализация Use Case.
        
        Args:
            person_repository: Репозиторий для работы с персонами
        """
        self._person_repository = person_repository
    
    def execute(self, dto: CreatePersonDTO) -> Person:
        """
        Выполнить создание персоны.
        
        Args:
            dto: Данные для создания персоны
            
        Returns:
            Созданная персона
            
        Raises:
            ValueError: Если данные невалидны или нарушают бизнес-правила
        """
        # 1. Валидация данных
        if not dto.first_name or not dto.last_name:
            raise ValueError("Имя и фамилия обязательны")
        
        # 2. Бизнес-правило: проверка дат
        if dto.date_of_death and dto.date_of_birth:
            if dto.date_of_death < dto.date_of_birth:
                raise ValueError("Дата смерти не может быть раньше даты рождения")
        
        # 3. Проверка на дубликаты (опционально)
        existing = self._person_repository.search(
            f"{dto.first_name} {dto.last_name}"
        )
        # Можно добавить проверку на дубликаты
        
        # 4. Создание доменной сущности
        person = Person(
            id=None,  # Будет присвоен при сохранении
            first_name=dto.first_name,
            last_name=dto.last_name,
            middle_name=dto.middle_name,
            date_of_birth=dto.date_of_birth,
            date_of_death=dto.date_of_death,
            gender=dto.gender,
            biography=dto.biography
        )
        
        # 5. Сохранение через репозиторий
        return self._person_repository.create(person)
```

### Использование в API

```python
# api/routes/persons.py

from fastapi import APIRouter, Depends
from core.application.use_cases.person.create_person import CreatePersonUseCase
from core.infrastructure.database.repositories.person_repository_impl import PersonRepositoryImpl
from api.dependencies.database import get_db_session

router = APIRouter(prefix="/persons", tags=["Persons"])

@router.post("/")
def create_person(dto: CreatePersonDTO, db = Depends(get_db_session)):
    """Создать новую персону через API."""
    # Создаем репозиторий
    repo = PersonRepositoryImpl(db)
    
    # Создаем Use Case
    use_case = CreatePersonUseCase(repo)
    
    # Выполняем операцию
    person = use_case.execute(dto)
    
    return person
```

### Использование в Desktop

```python
# desktop/controllers/person_controller.py

from core.application.use_cases.person.create_person import CreatePersonUseCase
from core.infrastructure.database.repositories.person_repository_impl import PersonRepositoryImpl

class PersonController:
    """Контроллер для работы с персонами в Desktop."""
    
    def __init__(self, db_session):
        repo = PersonRepositoryImpl(db_session)
        self._create_use_case = CreatePersonUseCase(repo)
    
    def create_person(self, first_name, last_name, ...):
        """Создать персону из UI формы."""
        dto = CreatePersonDTO(
            first_name=first_name,
            last_name=last_name,
            # ...
        )
        # Используем тот же Use Case!
        return self._create_use_case.execute(dto)
```

## ✅ Преимущества Use Cases

### 1. Переиспользование кода
```python
# Один Use Case используется везде:
CreatePersonUseCase → API
CreatePersonUseCase → Desktop  
CreatePersonUseCase → Mobile (в будущем)
```

### 2. Легкое тестирование
```python
# Можно мокировать репозиторий
mock_repo = Mock(spec=IPersonRepository)
use_case = CreatePersonUseCase(mock_repo)
result = use_case.execute(dto)
# Проверяем результат
```

### 3. Четкая бизнес-логика
```python
# Вся бизнес-логика в одном месте
# Не размазана по API роутам и UI контроллерам
```

### 4. Независимость от интерфейса
```python
# Use Case не знает, откуда его вызывают:
# - из API?
# - из Desktop?
# - из Mobile?
# Ему все равно!
```

## 📋 Типичные Use Cases для Family Tree

### Персоны (Person)
- `CreatePersonUseCase` - создать персону
- `GetPersonUseCase` - получить персону по ID
- `UpdatePersonUseCase` - обновить данные персоны
- `DeletePersonUseCase` - удалить персону
- `SearchPersonUseCase` - поиск персон

### Связи (Relationship)
- `AddRelationshipUseCase` - добавить связь (родитель, супруг, ребенок)
- `GetFamilyTreeUseCase` - получить генеалогическое дерево
- `RemoveRelationshipUseCase` - удалить связь

### Пользователи (User)
- `CreateUserUseCase` - создать пользователя
- `AuthenticateUserUseCase` - аутентификация
- `GetUserUseCase` - получить пользователя

## 🎓 Сравнение: БЕЗ Use Cases vs С Use Cases

### ❌ БЕЗ Use Cases (старый подход)

```python
# API Route
@router.post("/persons")
def create_person(dto, db):
    # Валидация
    if not dto.first_name:
        raise ValueError("...")
    
    # Бизнес-логика
    if dto.date_of_death < dto.date_of_birth:
        raise ValueError("...")
    
    # Создание
    person = Person(...)
    db.add(person)
    db.commit()
    return person

# Desktop Controller
def create_person(self, form_data):
    # ТА ЖЕ валидация (дублирование!)
    if not form_data.first_name:
        raise ValueError("...")
    
    # ТА ЖЕ бизнес-логика (дублирование!)
    if form_data.date_of_death < form_data.date_of_birth:
        raise ValueError("...")
    
    # Создание
    person = Person(...)
    # ...
```

**Проблемы:**
- ❌ Дублирование кода
- ❌ Сложно тестировать
- ❌ Изменения нужно делать в нескольких местах

### ✅ С Use Cases (новый подход)

```python
# Use Case (один раз)
class CreatePersonUseCase:
    def execute(self, dto):
        # Вся логика здесь
        ...

# API Route
@router.post("/persons")
def create_person(dto, db):
    use_case = CreatePersonUseCase(repo)
    return use_case.execute(dto)

# Desktop Controller
def create_person(self, form_data):
    use_case = CreatePersonUseCase(repo)
    return use_case.execute(dto)
```

**Преимущества:**
- ✅ Нет дублирования
- ✅ Легко тестировать
- ✅ Изменения в одном месте

## 🔄 Поток данных

```
1. Пользователь → API/Desktop
   ↓
2. Route/Controller → Use Case
   ↓
3. Use Case → Repository
   ↓
4. Repository → Database
   ↓
5. Database → Repository → Use Case → Route → Пользователь
```

## 💡 Резюме

**Use Case = Бизнес-операция**

- 📦 Инкапсулирует бизнес-логику
- 🔄 Переиспользуется в разных интерфейсах
- 🧪 Легко тестируется
- 🎯 Один Use Case = одна бизнес-операция

**Примеры:**
- "Создать персону" → `CreatePersonUseCase`
- "Получить дерево" → `GetFamilyTreeUseCase`
- "Добавить связь" → `AddRelationshipUseCase`

---

**Теперь понятно?** Use Cases — это ваша бизнес-логика, которая работает одинаково везде! 🚀
