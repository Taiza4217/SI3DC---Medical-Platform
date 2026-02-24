"""SI3DC — Redis Client for Clinical Cache.

Async Redis client wrapper for caching patient data and AI summaries.
"""

from __future__ import annotations

from typing import Optional

import structlog
from redis.asyncio import Redis

from backend.config import get_settings

logger = structlog.get_logger(__name__)

_redis: Optional[Redis] = None


async def init_redis() -> None:
    """Initialize the Redis connection."""
    global _redis
    settings = get_settings()
    try:
        _redis = Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
            retry_on_timeout=True,
        )
        await _redis.ping()
        logger.info("redis_connected", url=settings.REDIS_URL)
    except Exception as e:
        logger.warning("redis_connection_failed", error=str(e))
        _redis = None


async def close_redis() -> None:
    """Close the Redis connection."""
    global _redis
    if _redis:
        await _redis.close()
        logger.info("redis_closed")


def get_redis() -> Optional[Redis]:
    """Get the Redis client instance (may be None if unavailable)."""
    return _redis


async def cache_get(key: str) -> Optional[str]:
    """Get a value from Redis cache. Returns None if Redis is down."""
    if _redis is None:
        return None
    try:
        return await _redis.get(key)
    except Exception as e:
        logger.warning("redis_get_error", key=key, error=str(e))
        return None


async def cache_set(key: str, value: str, ttl: Optional[int] = None) -> bool:
    """Set a value in Redis cache. Returns False if Redis is down."""
    if _redis is None:
        return False
    try:
        settings = get_settings()
        await _redis.set(key, value, ex=ttl or settings.REDIS_CACHE_TTL)
        return True
    except Exception as e:
        logger.warning("redis_set_error", key=key, error=str(e))
        return False


async def cache_delete(key: str) -> bool:
    """Delete a key from Redis cache."""
    if _redis is None:
        return False
    try:
        await _redis.delete(key)
        return True
    except Exception as e:
        logger.warning("redis_delete_error", key=key, error=str(e))
        return False
