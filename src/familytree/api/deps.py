"""FastAPI dependencies for database sessions."""

from __future__ import annotations

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from familytree.core.database import SessionLocal


def get_db_session() -> Generator[Session, None, None]:
    """Yield a database session and close it after the request."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# Type alias for annotated dependencies
DBSession = Annotated[Session, Depends(get_db_session)]
