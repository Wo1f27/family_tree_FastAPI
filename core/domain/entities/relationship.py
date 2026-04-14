from datetime import datetime, UTC
from dataclasses import dataclass
from enum import Enum


class RelationshipType(str, Enum):
    PARENT = 'parent'
    CHILD = 'child'
    SPOUSE = 'spouse'
    SIBLING = 'sibling'
    OTHER = 'other'


@dataclass
class Relationship:
    id: int | None
    person_1: int
    person_2: int
    relationship_type: RelationshipType
    start_date: datetime | None
    end_date: datetime | None

    def __post_init__(self):
        if self.person_1 == self.person_2:
            raise ValueError('Персона не может быть родственником самому себе')
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError('Дата начала не может быть позже даты завершения')
        if self.start_date and self.start_date > datetime.now(UTC):
            raise ValueError('Дата начала не может быть в будущем')

    @property
    def is_alive(self) -> bool:
        return self.end_date is None

    def get_reverse_type(self) -> RelationshipType:
        reverse_map = {
            RelationshipType.PARENT: RelationshipType.CHILD,
            RelationshipType.CHILD: RelationshipType.PARENT,
            RelationshipType.SPOUSE: RelationshipType.SPOUSE,
            RelationshipType.SIBLING: RelationshipType.SIBLING,
            RelationshipType.OTHER: RelationshipType.OTHER
        }
        return reverse_map[self.relationship_type]




