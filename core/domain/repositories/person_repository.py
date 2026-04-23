from abc import ABC, abstractmethod
from core.domain.entities import Person


class PersonRepository(ABC):
    """Интерфейс репозитория для работы с персонами"""
    @abstractmethod
    def get_by_id(self, person_id: int) -> Person | None:
        pass

    @abstractmethod
    def create(self, person: Person) -> Person:
        pass

    @abstractmethod
    def update(self, person: Person) -> Person:
        pass

    @abstractmethod
    def delete(self, person_id: int) -> bool:
        pass

    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> list[Person]:
        pass
