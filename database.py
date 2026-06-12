import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, text
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


# (таблица, колонка, тип SQLite) — добавляются при обновлении старой БД без потери данных.
_SQLITE_COLUMN_MIGRATIONS: tuple[tuple[str, str, str], ...] = (
    ('phones', 'created_at', 'DATETIME'),
    ('phones', 'updated_at', 'DATETIME'),
    ('addresses', 'created_at', 'DATETIME'),
    ('addresses', 'updated_at', 'DATETIME'),
)


def _sqlite_table_exists(conn, table: str) -> bool:
    row = conn.execute(
        text("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = :name"),
        {'name': table},
    ).first()
    return row is not None


def _sqlite_column_names(conn, table: str) -> set[str]:
    rows = conn.execute(text(f'PRAGMA table_info("{table}")')).fetchall()
    return {row[1] for row in rows}


def _apply_sqlite_migrations() -> None:
    """Добавить недостающие колонки в существующие таблицы (SQLite)."""
    if engine.dialect.name != 'sqlite':
        return

    with engine.begin() as conn:
        for table, column, col_type in _SQLITE_COLUMN_MIGRATIONS:
            if not _sqlite_table_exists(conn, table):
                continue
            if column in _sqlite_column_names(conn, table):
                continue
            conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN "{column}" {col_type}'))


def init_db() -> None:
    # Регистрация моделей в metadata перед create_all.
    import models  # noqa: F401

    Base.metadata.create_all(engine)
    _apply_sqlite_migrations()
