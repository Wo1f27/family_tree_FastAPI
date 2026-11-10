"""Application settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # DB URL (highest priority)
    db_url: str | None = None

    # Individual DB params (used when db_url is not set)
    db_host: str = "127.0.0.1"
    db_port: int = 5432
    db_name: str = "familytree"
    db_user: str = "familytree"
    db_password: str = ""

    # SQLite fallback
    db_path: str = "data/genealogy.db"

    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = False

    model_config = {"env_prefix": "FAMILY_TREE_", "env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def use_postgresql(self) -> bool:
        """True if db_url is set, or if individual DB params are non-default."""
        if self.db_url:
            return True
        if self.db_name != "familytree" or self.db_user != "familytree":
            return True
        if self.db_password:
            return True
        return False

    @property
    def resolved_db_url(self) -> str:
        """Return the final database URL to use."""
        if self.db_url:
            return self.db_url
        if self.use_postgresql:
            return (
                f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
                f"@{self.db_host}:{self.db_port}/{self.db_name}"
            )
        # SQLite fallback
        return f"sqlite:///{self.db_path}"


settings = Settings()
