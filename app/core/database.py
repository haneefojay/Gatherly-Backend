from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.core.settings import get_settings

settings = get_settings()

engine = create_async_engine(
    url=settings.POSTGRES_DATABASE_URL,
    pool_pre_ping=True,
    pool_size=100,
    max_overflow=50,
)


AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Synchronous engine for Celery workers (Celery does not support async).
# Converts 'postgresql+asyncpg://...' -> 'postgresql+psycopg2://...'
_sync_url = settings.POSTGRES_DATABASE_URL.replace("+asyncpg", "").replace(
    "postgresql+asyncpg", "postgresql"
)
sync_engine = create_engine(_sync_url, pool_pre_ping=True)

SyncSessionLocal = sessionmaker(
    bind=sync_engine,
    class_=Session,
    expire_on_commit=False,
)

DBBase = declarative_base()
