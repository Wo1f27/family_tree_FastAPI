"""
Зависимости для работы с базой данных.
"""
from typing import Generator
from sqlalchemy.orm import Session
from core.infrastructure.database.config import get_db


def get_db_session() -> Generator[Session, None, None]:
    """
    Получить сессию базы данных.
    
    Используется как зависимость в FastAPI роутах.
    
    Yields:
        Session: SQLAlchemy сессия
    """
    yield from get_db()
