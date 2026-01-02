# type: ignore
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """The settings for the application."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    DEBUG: bool = False
    TESTING: bool = False
    ALLOW_NON_TEST_DB: bool = False

    # Logfire
    LOGFIRE_TOKEN: str | None = None

    # DB Settings
    POSTGRES_DATABASE_URL: str

    # DB Settings for testing
    POSTGRES_TEST_DATABASE_URL: str | None = None

    # REDIS
    REDIS_BROKER_URL: str

    # JWT
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REQ_RATE: int = 30
    REQ_RATE_TIME: int = 3600
    REQ_RATE_USER: int = 100
    REQ_RATE_ADMIN: int = 500
    REQ_RATE_ORGANIZER: int = 200


@lru_cache
def get_settings():
    """This function returns the settings obj for the application."""
    return Settings()
