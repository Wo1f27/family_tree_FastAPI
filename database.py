"""SQLite storage for desktop Family Tree.

Updater contract (важно для инсталлятора / автообновления):
- Файл БД лежит в пользовательском каталоге (LOCALAPPDATA/…), НЕ рядом с exe.
- Обновление приложения НЕ должно удалять/перезаписывать этот каталог.
- При старте: create_all (новые таблицы) + ADD COLUMN (новые поля).
- Существующие строки и значения не трогаем; DROP/пересоздание таблиц запрещены.
- Перед миграцией колонок делается резервная копия genealogy.db → .bak
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Увеличивать при добавлении колонок/таблиц в _SQLITE_COLUMN_MIGRATIONS / моделей.
SCHEMA_VERSION = 4


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
DB_PATH = DATA_DIR / 'genealogy.db'

_engine_echo = (not getattr(sys, 'frozen', False)) and os.environ.get('FAMILY_TREE_DEBUG_SQL', '').lower() in (
    '1',
    'true',
    'yes',
)

engine = create_engine(
    f'sqlite:///{DB_PATH}',
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


# (таблица, колонка, тип SQLite) — только ADD COLUMN, без изменения/удаления старых.
_SQLITE_COLUMN_MIGRATIONS: tuple[tuple[str, str, str], ...] = (
    ('persons', 'place_of_birth', 'VARCHAR(255)'),
    ('persons', 'place_of_death', 'VARCHAR(255)'),
    ('persons', 'burial_place', 'VARCHAR(255)'),
    ('persons', 'death_cause', 'VARCHAR(20)'),
    ('persons', 'maiden_name', 'VARCHAR(100)'),
    ('persons', 'archive_records', 'TEXT'),
    ('persons', 'birth_year', 'INTEGER'),
    ('persons', 'birth_month', 'INTEGER'),
    ('persons', 'birth_day', 'INTEGER'),
    ('persons', 'birth_approx', 'INTEGER DEFAULT 0'),
    ('persons', 'death_year', 'INTEGER'),
    ('persons', 'death_month', 'INTEGER'),
    ('persons', 'death_day', 'INTEGER'),
    ('persons', 'death_approx', 'INTEGER DEFAULT 0'),
    ('phones', 'created_at', 'DATETIME'),
    ('phones', 'updated_at', 'DATETIME'),
    ('addresses', 'created_at', 'DATETIME'),
    ('addresses', 'updated_at', 'DATETIME'),
    ('addresses', 'kind', "VARCHAR(20) DEFAULT 'current'"),
    ('addresses', 'period_note', 'VARCHAR(100)'),
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


def _backup_db_if_needed() -> None:
    """Одна резервная копия перед ALTER — на случай сбоя обновления."""
    if not DB_PATH.is_file():
        return
    bak = DB_PATH.with_suffix('.db.bak')
    try:
        shutil.copy2(DB_PATH, bak)
    except OSError:
        # Не блокируем запуск, если бэкап не удался (нет места и т.п.).
        pass


def _ensure_schema_meta(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS schema_meta (
                key TEXT PRIMARY KEY NOT NULL,
                value TEXT NOT NULL
            )
            """
        )
    )
    row = conn.execute(
        text("SELECT value FROM schema_meta WHERE key = 'schema_version'")
    ).first()
    if row is None:
        conn.execute(
            text("INSERT INTO schema_meta (key, value) VALUES ('schema_version', :v)"),
            {'v': str(SCHEMA_VERSION)},
        )
    else:
        conn.execute(
            text("UPDATE schema_meta SET value = :v WHERE key = 'schema_version'"),
            {'v': str(SCHEMA_VERSION)},
        )


def _apply_sqlite_migrations() -> None:
    """Добавить недостающие колонки в существующие таблицы (SQLite), данные сохранить."""
    if engine.dialect.name != 'sqlite':
        return

    pending = False
    with engine.connect() as conn:
        for table, column, _col_type in _SQLITE_COLUMN_MIGRATIONS:
            if not _sqlite_table_exists(conn, table):
                continue
            if column not in _sqlite_column_names(conn, table):
                pending = True
                break

    if pending:
        _backup_db_if_needed()

    with engine.begin() as conn:
        for table, column, col_type in _SQLITE_COLUMN_MIGRATIONS:
            if not _sqlite_table_exists(conn, table):
                continue
            if column in _sqlite_column_names(conn, table):
                continue
            conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN "{column}" {col_type}'))
        # Старые адреса без kind считаем «сейчас».
        if _sqlite_table_exists(conn, 'addresses') and 'kind' in _sqlite_column_names(conn, 'addresses'):
            conn.execute(
                text("UPDATE addresses SET kind = 'current' WHERE kind IS NULL OR kind = ''")
            )
        _backfill_partial_dates_from_legacy(conn)
        _ensure_schema_meta(conn)


def _backfill_partial_dates_from_legacy(conn) -> None:
    """Разложить уже лежащие date_of_birth/death в year/month/day (один раз для пустых)."""
    if not _sqlite_table_exists(conn, 'persons'):
        return
    cols = _sqlite_column_names(conn, 'persons')
    needed = {
        'date_of_birth',
        'date_of_death',
        'birth_year',
        'birth_month',
        'birth_day',
        'birth_approx',
        'death_year',
        'death_month',
        'death_day',
        'death_approx',
    }
    if not needed.issubset(cols):
        return

    # SQLite хранит DATE как текст YYYY-MM-DD — strftime работает.
    conn.execute(
        text(
            """
            UPDATE persons
            SET
                birth_year = CAST(strftime('%Y', date_of_birth) AS INTEGER),
                birth_month = CAST(strftime('%m', date_of_birth) AS INTEGER),
                birth_day = CAST(strftime('%d', date_of_birth) AS INTEGER),
                birth_approx = 0
            WHERE date_of_birth IS NOT NULL
              AND birth_year IS NULL
            """
        )
    )
    conn.execute(
        text(
            """
            UPDATE persons
            SET
                death_year = CAST(strftime('%Y', date_of_death) AS INTEGER),
                death_month = CAST(strftime('%m', date_of_death) AS INTEGER),
                death_day = CAST(strftime('%d', date_of_death) AS INTEGER),
                death_approx = 0
            WHERE date_of_death IS NOT NULL
              AND death_year IS NULL
            """
        )
    )


def init_db() -> None:
    # Регистрация моделей в metadata перед create_all.
    import models  # noqa: F401

    # Только создаёт отсутствующие таблицы — существующие не удаляет и не чистит.
    Base.metadata.create_all(engine)
    _apply_sqlite_migrations()
