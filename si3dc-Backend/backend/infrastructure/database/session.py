"""SI3DC — Database Session Management.

Async SQLAlchemy engine, session factory, and lifecycle hooks.
"""

from __future__ import annotations

from typing import AsyncGenerator
from urllib.parse import urlparse, quote_plus

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.config import get_settings

logger = structlog.get_logger(__name__)

_engine = None
_session_factory = None


def _safe_db_url(raw_url: str) -> str:
    """URL-encode user/password for asyncpg compatibility.

    Supabase pooler uses dotted usernames (e.g. postgres.projectref)
    which asyncpg misparses. URL-encoding fixes this.
    """
    parsed = urlparse(raw_url)
    if not parsed.username:
        return raw_url
    user = quote_plus(parsed.username)
    password = quote_plus(parsed.password or "")
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
    dbname = parsed.path.lstrip("/")
    scheme = parsed.scheme or "postgresql+asyncpg"
    return f"{scheme}://{user}:{password}@{host}:{port}/{dbname}"


async def init_db() -> None:
    """Initialize the async database engine and session factory."""
    global _engine, _session_factory
    settings = get_settings()

    # asyncpg misparses dotted usernames (e.g. postgres.projectref)
    # URL-encode user/password to ensure correct parsing
    db_url = _safe_db_url(settings.DATABASE_URL)

    _engine = create_async_engine(
        db_url,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        echo=settings.DB_ECHO,
        pool_pre_ping=True,
        pool_recycle=300,
    )
    _session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    logger.info("database_initialized", host=settings.DATABASE_URL.split("@")[-1])


async def close_db() -> None:
    """Dispose of the database engine."""
    global _engine
    if _engine:
        await _engine.dispose()
        logger.info("database_closed")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session."""
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
