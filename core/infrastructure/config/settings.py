"""
Настройки приложения из переменных окружения.
"""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения."""
    
    # Database settings
    DB_HOST: str
    DB_PORT: str
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    
    # Auth settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 1
    
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True
    )


def get_db_url() -> str:
    """Получить URL для подключения к базе данных."""
    settings = Settings()
    return (
        f"postgresql+psycopg2://{settings.DB_USER}:{settings.DB_PASSWORD}@"
        f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )


def get_auth_data() -> dict:
    """Получить данные для аутентификации."""
    settings = Settings()
    return {
        'secret_key': settings.SECRET_KEY,
        'algorithm': settings.ALGORITHM
    }
