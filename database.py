import os
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


def _user_data_root() -> Path:
    """Writable folder that survives app reinstalls (installer overwrites Program Files only)."""
    if sys.platform == 'win32':
        base = os.environ.get('LOCALAPPDATA')
        if base:
            return Path(base) / 'FamilyTree'
        return Path.home() / 'AppData' / 'Local' / 'FamilyTree'
    if sys.platform == 'darwin':
        return Path.home() / 'Library' / 'Application Support' / 'FamilyTree'
    return Path.home() / '.local' / 'share' / 'FamilyTree'


def _resolve_data_dir() -> Path:
    # Frozen (PyInstaller etc.): never keep DB next to the exe in Program Files.
    if getattr(sys, 'frozen', False):
        return _user_data_root() / 'data'
    # Development: project directory (as before).
    return Path(__file__).resolve().parent / 'data'


DATA_DIR = _resolve_data_dir()
DATA_DIR.mkdir(parents=True, exist_ok=True)

_engine_echo = (not getattr(sys, 'frozen', False)) and os.environ.get('FAMILY_TREE_DEBUG_SQL', '').lower() in (
    '1',
    'true',
    'yes',
)

engine = create_engine(
    f'sqlite:///{DATA_DIR / "genealogy.db"}',
    echo=_engine_echo,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


def init_db():
    Base.metadata.create_all(engine)
