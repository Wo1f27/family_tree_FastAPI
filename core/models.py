"""
Чистые модели данных без зависимости от БД
"""

from dataclasses import dataclass, field
from datetime import datetime, date
import uuid


class Gender:
    MALE = 1
    FEMALE = 2
    OTHER = 3
    UNKNOWN = 4


@dataclass
class Person:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    first_name: str = ''
    last_name: str = ''
    middle_name: str = ''
    gender: Gender = Gender.UNKNOWN

    birth_date: date = None
    birth_place: str = None
    death_date: date = None
    death_place: str = None

    father_id: int | None = None
    mother_id: int | None = None
    spouse_ids: list[int] | None = None
    children_ids: list[int] | None = None

    biography: str = ''
    photo_url: str | None = None

    version: int = 1
    created_on: datetime = field(default_factory=lambda: datetime.today().isoformat())
    updated_on: datetime = field(default_factory=lambda: datetime.today().isoformat())


