from dataclasses import dataclass, field
from datetime import datetime, date, UTC
from enum import Enum


class Gender(str, Enum):
    MALE = 'male'
    FEMALE = 'female'
    OTHER = 'other'


@dataclass
class Person:
    id: int | None
    first_name: str
    last_name: str
    middle_name: str | None
    date_birth: date | None
    date_death: date | None
    gender: str
    biography: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC), init=False)
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC), init=False)

    def __post_init__(self):
        if not self.first_name or not self.last_name:
            raise ValueError('Имя и фамилия обязательны')
        if self.date_death and self.date_birth:
            if self.date_death < self.date_birth:
                raise ValueError('Дата смерти не может быть раньше даты рождения')

    @property
    def full_name(self) -> str:
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return ' '.join(parts)

    @property
    def name(self) -> str:
        return f'{self.first_name} {self.last_name}'

    @property
    def age(self) -> int | None:
        if not self.date_birth:
            return None
        end = self.date_death or date.today()
        return end.year - self.date_birth.year - (
            (end.month, end.day) < (self.date_birth.month, self.date_birth.day)
        )

    @property
    def is_alive(self) -> bool:
        return self.date_death is None
