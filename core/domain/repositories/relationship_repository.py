from abc import ABC, abstractmethod
from core.domain.entities import Relationship, RelationshipType


class RelationshipRepository(ABC):
    """Интерфейс репозитория для работы с отношениями"""
    @abstractmethod
    def create(self, relationship: Relationship) -> Relationship:
        pass

    @abstractmethod
    def get_by_id(self, relationship_id: int) -> Relationship | None:
        pass

    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> list[Relationship]:
        pass

    @abstractmethod
    def update(self, relationship: Relationship) -> Relationship:
        pass

    @abstractmethod
    def delete(self, relationship_id: int) -> bool:
        pass

    @abstractmethod
    def get_by_person_id(self, person_id: int) -> list[Relationship]:
        pass

    @abstractmethod
    def get_by_type(self, person_id: int, relationship_type: RelationshipType) -> list[Relationship]:
        pass

