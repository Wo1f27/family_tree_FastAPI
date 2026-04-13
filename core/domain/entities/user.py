from dataclasses import dataclass, field
from datetime import date, datetime, UTC


@dataclass
class User:
    id: int | None
    username: str
    password_hash: str
    email: str
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC), init=False)
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC), init=False)

    def __post_init__(self):
        if '@' not in self.email:
            raise ValueError('Некорректный email адрес')
        if len(self.username) < 2:
            raise ValueError('Никнейм минимум 2 символа')

    @property
    def is_authenticated(self) -> bool:
        return self.is_active