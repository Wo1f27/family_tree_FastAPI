"""Application settings."""

from __future__ import annotations

import sys
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_path: str = "data/genealogy.db"
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False

    model_config = {"env_prefix": "FAMILY_TREE_"}


def get_db_path() -> Path:
    """Resolve database path for web app (shared with desktop)."""
    if getattr(sys, 'frozen', False):
        # PyInstaller: use user data folder
        user_root = Path.home() / '.local' / 'share' / 'FamilyTree'
        db_dir = user_root / 'data'
        db_dir.mkdir(parents=True, exist_ok=True)
        return db_dir / 'genealogy.db'
    # Development: project directory (shared with desktop via symlink)
    return Path(__file__).resolve().parent.parent.parent.parent / 'data' / 'genealogy.db'


settings = Settings()
