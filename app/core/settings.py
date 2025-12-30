# type: ignore
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """The settings for the application."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    DEBUG: bool = True

    # Logfire
    LOGFIRE_TOKEN: str | None = None

    # DB Settings
    POSTGRES_DATABASE_URL: str

    # REDIS
    REDIS_BROKER_URL: str

    # JWT
    SECRET_KEY: str


@lru_cache
def get_settings():
    """This function returns the settings obj for the application."""
    return Settings()
