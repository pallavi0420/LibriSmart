import sys
from typing import AsyncGenerator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine
)
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

def get_async_database_url() -> str:
    """Returns async-compatible database URL with appropriate driver prefix."""
    url = settings.DATABASE_URL
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


# Engine setup
engine = create_async_engine(
    get_async_database_url(),
    echo=False,
    future=True,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy ORM models."""
    pass


def get_sync_database_url() -> str:
    """Returns a synchronous version of the DATABASE_URL for migrations and DDL setup."""
    url = settings.DATABASE_URL
    if "sqlite+aiosqlite" in url:
        return url.replace("sqlite+aiosqlite", "sqlite")
    if "postgresql+asyncpg" in url:
        return url.replace("postgresql+asyncpg", "postgresql+psycopg2")
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    if url.startswith("postgresql://") and not url.startswith("postgresql+"):
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def create_all_tables_sync():
    """Synchronously creates all database tables from Base.metadata."""
    sync_url = get_sync_database_url()
    sync_engine = create_engine(
        sync_url,
        connect_args={"check_same_thread": False} if "sqlite" in sync_url else {}
    )
    Base.metadata.create_all(bind=sync_engine)
    sync_engine.dispose()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an independent database session per request
    and guarantees safe closure/rollback upon completion.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
