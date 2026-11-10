"""Database layer for Family Tree Web API.

Supports both SQLite (default) and PostgreSQL (configured via FAMILY_TREE_DB_URL or individual env vars).
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker


# ---------------------------------------------------------------------------
# Lazy import of settings (avoids circular imports)
# ---------------------------------------------------------------------------

def _get_settings():
    from familytree.core.config import settings
    return settings


# ---------------------------------------------------------------------------
# Engine & Session
# ---------------------------------------------------------------------------

def _get_engine():
    """Create SQLAlchemy engine based on configured DB URL."""
    settings = _get_settings()
    url = settings.resolved_db_url

    # Ensure data directory exists for SQLite
    if url.startswith('sqlite'):
        # Extract path from sqlite:///path/to/db
        db_path = url.replace('sqlite:///', '')
        db_dir = Path(db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    # Echo SQL in debug mode
    echo = os.environ.get('FAMILY_TREE_DEBUG_SQL', '').lower() in ('1', 'true', 'yes')

    # PostgreSQL-specific options
    if url.startswith('postgresql'):
        echo_pool = echo
    else:
        echo_pool = False

    return create_engine(url, echo=echo, echo_pool=echo_pool)


def _get_session_factory(engine):
    return sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )


# Module-level engine and session (initialized at import time)
_engine = _get_engine()
SessionLocal = _get_session_factory(_engine)


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# SQLite inline migrations (preserved for backward compatibility)
# ---------------------------------------------------------------------------

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
    """Backup before ALTER -- in case of update failure."""
    settings = _get_settings()
    db_path = Path(settings.db_path)
    if not db_path.is_file():
        return
    bak = db_path.with_suffix('.db.bak')
    try:
        shutil.copy2(db_path, bak)
    except OSError:
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
            {'v': '4'},
        )
    else:
        conn.execute(
            text("UPDATE schema_meta SET value = :v WHERE key = 'schema_version'"),
            {'v': '4'},
        )


def _backfill_partial_dates_from_legacy(conn) -> None:
    """Split existing date_of_birth/death into year/month/day (once for empty rows)."""
    if not _sqlite_table_exists(conn, 'persons'):
        return
    cols = _sqlite_column_names(conn, 'persons')
    needed = {
        'date_of_birth', 'date_of_death',
        'birth_year', 'birth_month', 'birth_day', 'birth_approx',
        'death_year', 'death_month', 'death_day', 'death_approx',
    }
    if not needed.issubset(cols):
        return

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


def _apply_sqlite_migrations() -> None:
    """Add missing columns in existing tables (SQLite only), preserve data."""
    if _engine.dialect.name != 'sqlite':
        return

    pending = False
    with _engine.connect() as conn:
        for table, column, _col_type in _SQLITE_COLUMN_MIGRATIONS:
            if not _sqlite_table_exists(conn, table):
                continue
            if column not in _sqlite_column_names(conn, table):
                pending = True
                break

    if pending:
        _backup_db_if_needed()

    with _engine.begin() as conn:
        for table, column, col_type in _SQLITE_COLUMN_MIGRATIONS:
            if not _sqlite_table_exists(conn, table):
                continue
            if column in _sqlite_column_names(conn, table):
                continue
            conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN "{column}" {col_type}'))
        # Old addresses without kind are considered "current"
        if _sqlite_table_exists(conn, 'addresses') and 'kind' in _sqlite_column_names(conn, 'addresses'):
            conn.execute(
                text("UPDATE addresses SET kind = 'current' WHERE kind IS NULL OR kind = ''")
            )
        _backfill_partial_dates_from_legacy(conn)
        _ensure_schema_meta(conn)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def init_db() -> None:
    """Create missing tables and apply column migrations.

    IMPORTANT: Must be called AFTER all models are imported
    so that Base.metadata knows about all table definitions.

    For SQLite: creates tables + applies inline column migrations.
    For PostgreSQL: creates tables only (migrations handled by Alembic).
    """
    if _engine.dialect.name == 'sqlite':
        Base.metadata.create_all(_engine)
        _apply_sqlite_migrations()
    else:
        # PostgreSQL: just ensure tables exist (Alembic handles schema changes)
        Base.metadata.create_all(_engine)


# Expose engine for Alembic to use
engine = _engine
