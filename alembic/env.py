"""Alembic environment configuration."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Import app components
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from familytree.core.database import Base  # noqa: F401
from familytree.core.config import settings  # noqa: F401

# Alembic Config object
config = context.config

# Override sqlalchemy.url from env vars if set
import os

db_url = os.environ.get("FAMILY_TREE_DB_URL")
if not db_url:
    # Check if PostgreSQL is configured (any non-default param means PostgreSQL)
    db_host = os.environ.get("FAMILY_TREE_DB_HOST", settings.db_host)
    db_port = os.environ.get("FAMILY_TREE_DB_PORT", str(settings.db_port))
    db_name = os.environ.get("FAMILY_TREE_DB_NAME", settings.db_name)
    db_user = os.environ.get("FAMILY_TREE_DB_USER", settings.db_user)
    db_password = os.environ.get("FAMILY_TREE_DB_PASSWORD", settings.db_password)

    # Detect PostgreSQL: if any param differs from defaults, or DB_URL-like params are set
    is_postgresql = (
        db_name != "familytree"
        or db_user != "familytree"
        or db_password != ""
        or db_host != "127.0.0.1"
    )
    if is_postgresql:
        db_url = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

if db_url:
    config.set_main_option("sqlalchemy.url", db_url)

# Logging config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata

# Tables to exclude from Alembic autogenerate
# schema_meta is used only for SQLite inline migrations, not a SQLAlchemy model
def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table" and name == "schema_meta":
        return False
    return True


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
