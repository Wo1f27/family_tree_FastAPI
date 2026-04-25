# Примеры реализации

## Пример 1: Создание персоны (Use Case)

### Domain Entity (core/domain/entities/person.py)
```python
from dataclasses import dataclass
from datetime import date
from typing import Optional

@dataclass
class Person:
    """Доменная сущность - человек в генеалогическом дереве"""
    id: Optional[int]
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    date_of_death: Optional[date] = None
    gender: Optional[str] = None
    biography: Optional[str] = None
    
    def __post_init__(self):
        if self.date_of_death and self.date_of_birth:
            if self.date_of_death < self.date_of_birth:
                raise ValueError("Дата смерти не может быть раньше даты рождения")
    
    @property
    def full_name(self) -> str:
        parts = [self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.last_name)
        return " ".join(parts)
```

### Repository Interface (core/domain/repositories/person_repository.py)
```python
from abc import ABC, abstractmethod
from typing import Optional, List
from core.domain.entities.person import Person

class IPersonRepository(ABC):
    """Интерфейс репозитория для работы с персонами"""
    
    @abstractmethod
    def create(self, person: Person) -> Person:
        """Создать персону"""
        pass
    
    @abstractmethod
    def get_by_id(self, person_id: int) -> Optional[Person]:
        """Получить персону по ID"""
        pass
    
    @abstractmethod
    def update(self, person: Person) -> Person:
        """Обновить персону"""
        pass
    
    @abstractmethod
    def delete(self, person_id: int) -> bool:
        """Удалить персону"""
        pass
    
    @abstractmethod
    def search(self, query: str) -> List[Person]:
        """Поиск персон по имени"""
        pass
    
    @abstractmethod
    def get_all(self) -> List[Person]:
        """Получить всех персон"""
        pass
```

### Use Case (core/application/use_cases/person/create_person.py)
```python
from core.domain.entities.person import Person
from core.domain.repositories.person_repository import IPersonRepository
from core.application.dto.person_dto import CreatePersonDTO

class CreatePersonUseCase:
    """Use Case для создания персоны"""
    
    def __init__(self, person_repository: IPersonRepository):
        self._person_repository = person_repository
    
    def execute(self, dto: CreatePersonDTO) -> Person:
        """
        Создать новую персону
        
        Args:
            dto: Данные для создания персоны
            
        Returns:
            Созданная персона
            
        Raises:
            ValueError: Если данные невалидны
        """
        # Валидация бизнес-правил
        if not dto.first_name or not dto.last_name:
            raise ValueError("Имя и фамилия обязательны")
        
        # Создание доменной сущности
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
        
        # Сохранение через репозиторий
        return self._person_repository.create(person)
```

### DTO (core/application/dto/person_dto.py)
```python
from pydantic import BaseModel, Field
from datetime import date
from typing import Optional

class CreatePersonDTO(BaseModel):
    """DTO для создания персоны"""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    date_of_birth: Optional[date] = None
    date_of_death: Optional[date] = None
    gender: Optional[str] = Field(None, pattern="^(male|female|other)$")
    biography: Optional[str] = None

class PersonResponseDTO(BaseModel):
    """DTO для ответа с персоной"""
    id: int
    first_name: str
    last_name: str
    middle_name: Optional[str]
    full_name: str
    date_of_birth: Optional[date]
    date_of_death: Optional[date]
    gender: Optional[str]
    biography: Optional[str]
    
    class Config:
        from_attributes = True
```

### Repository Implementation (core/infrastructure/database/repositories/person_repository_impl.py)
```python
from typing import Optional, List
from sqlalchemy.orm import Session
from core.domain.entities.person import Person
from core.domain.repositories.person_repository import IPersonRepository
from core.infrastructure.database.models.person_model import PersonModel

class PersonRepositoryImpl(IPersonRepository):
    """Реализация репозитория персон через SQLAlchemy"""
    
    def __init__(self, db: Session):
        self._db = db
    
    def create(self, person: Person) -> Person:
        db_model = PersonModel(
            first_name=person.first_name,
            last_name=person.last_name,
            middle_name=person.middle_name,
            date_of_birth=person.date_of_birth,
            date_of_death=person.date_of_death,
            gender=person.gender,
            biography=person.biography
        )
        self._db.add(db_model)
        self._db.commit()
        self._db.refresh(db_model)
        return self._to_domain(db_model)
    
    def get_by_id(self, person_id: int) -> Optional[Person]:
        db_model = self._db.query(PersonModel).filter(PersonModel.id == person_id).first()
        return self._to_domain(db_model) if db_model else None
    
    def update(self, person: Person) -> Person:
        db_model = self._db.query(PersonModel).filter(PersonModel.id == person.id).first()
        if not db_model:
            raise ValueError(f"Person with id {person.id} not found")
        
        db_model.first_name = person.first_name
        db_model.last_name = person.last_name
        # ... обновление остальных полей
        
        self._db.commit()
        self._db.refresh(db_model)
        return self._to_domain(db_model)
    
    def delete(self, person_id: int) -> bool:
        db_model = self._db.query(PersonModel).filter(PersonModel.id == person_id).first()
        if db_model:
            self._db.delete(db_model)
            self._db.commit()
            return True
        return False
    
    def search(self, query: str) -> List[Person]:
        db_models = self._db.query(PersonModel).filter(
            (PersonModel.first_name.ilike(f"%{query}%")) |
            (PersonModel.last_name.ilike(f"%{query}%"))
        ).all()
        return [self._to_domain(model) for model in db_models]
    
    def get_all(self) -> List[Person]:
        db_models = self._db.query(PersonModel).all()
        return [self._to_domain(model) for model in db_models]
    
    def _to_domain(self, db_model: PersonModel) -> Person:
        """Преобразование DB модели в доменную сущность"""
        return Person(
            id=db_model.id,
            first_name=db_model.first_name,
            last_name=db_model.last_name,
            middle_name=db_model.middle_name,
            date_of_birth=db_model.date_of_birth,
            date_of_death=db_model.date_of_death,
            gender=db_model.gender,
            biography=db_model.biography
        )
```

## Пример 2: Использование в API

### API Route (api/routes/persons.py)
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.application.use_cases.person.create_person import CreatePersonUseCase
from core.application.use_cases.person.get_person import GetPersonUseCase
from core.infrastructure.database.repositories.person_repository_impl import PersonRepositoryImpl
from core.application.dto.person_dto import CreatePersonDTO, PersonResponseDTO
from api.dependencies.database import get_db

router = APIRouter(prefix="/persons", tags=["Persons"])

@router.post("/", response_model=PersonResponseDTO, status_code=status.HTTP_201_CREATED)
def create_person(dto: CreatePersonDTO, db: Session = Depends(get_db)):
    """Создать новую персону"""
    try:
        repo = PersonRepositoryImpl(db)
        use_case = CreatePersonUseCase(repo)
        person = use_case.execute(dto)
        return PersonResponseDTO.model_validate(person)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{person_id}", response_model=PersonResponseDTO)
def get_person(person_id: int, db: Session = Depends(get_db)):
    """Получить персону по ID"""
    repo = PersonRepositoryImpl(db)
    use_case = GetPersonUseCase(repo)
    person = use_case.execute(person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return PersonResponseDTO.model_validate(person)
```

## Пример 3: Использование в Desktop

### Desktop Controller (desktop/controllers/person_controller.py)
```python
from core.application.use_cases.person.create_person import CreatePersonUseCase
from core.application.use_cases.person.get_person import GetPersonUseCase
from core.infrastructure.database.repositories.person_repository_impl import PersonRepositoryImpl
from core.application.dto.person_dto import CreatePersonDTO
from sqlalchemy.orm import Session

class PersonController:
    """Контроллер для работы с персонами в Desktop приложении"""
    
    def __init__(self, db_session: Session):
        self._db = db_session
        repo = PersonRepositoryImpl(db_session)
        self._create_use_case = CreatePersonUseCase(repo)
        self._get_use_case = GetPersonUseCase(repo)
    
    def create_person(
        self,
        first_name: str,
        last_name: str,
        middle_name: str = None,
        date_of_birth: str = None,
        # ... другие параметры
    ):
        """Создать персону из UI формы"""
        dto = CreatePersonDTO(
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
            date_of_birth=date_of_birth,
            # ...
        )
        try:
            person = self._create_use_case.execute(dto)
            return person
        except ValueError as e:
            # Показать ошибку в UI
            raise
    
    def get_person(self, person_id: int):
        """Получить персону для отображения"""
        return self._get_use_case.execute(person_id)
```

### Desktop UI (desktop/ui/person_form.py) - пример для PyQt
```python
from PyQt6.QtWidgets import QDialog, QFormLayout, QLineEdit, QDateEdit, QPushButton
from desktop.controllers.person_controller import PersonController

class PersonFormDialog(QDialog):
    """Диалог создания/редактирования персоны"""
    
    def __init__(self, controller: PersonController, parent=None):
        super().__init__(parent)
        self._controller = controller
        self.setup_ui()
    
    def setup_ui(self):
        layout = QFormLayout()
        
        self.first_name_input = QLineEdit()
        self.last_name_input = QLineEdit()
        self.date_of_birth_input = QDateEdit()
        
        layout.addRow("Имя:", self.first_name_input)
        layout.addRow("Фамилия:", self.last_name_input)
        layout.addRow("Дата рождения:", self.date_of_birth_input)
        
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.save_person)
        layout.addRow(save_btn)
        
        self.setLayout(layout)
    
    def save_person(self):
        """Сохранить персону через контроллер"""
        try:
            person = self._controller.create_person(
                first_name=self.first_name_input.text(),
                last_name=self.last_name_input.text(),
                date_of_birth=self.date_of_birth_input.date().toPython()
            )
            self.accept()
        except ValueError as e:
            # Показать ошибку
            pass
```

## Преимущества такого подхода

✅ **Одна бизнес-логика** - `CreatePersonUseCase` используется и в API, и в Desktop  
✅ **Легкое тестирование** - можно мокировать `IPersonRepository`  
✅ **Гибкость** - можно заменить SQLAlchemy на другую БД, изменив только реализацию репозитория  
✅ **Чистая архитектура** - зависимости направлены внутрь, к ядру  
