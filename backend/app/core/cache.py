"""Redis caching utilities for hot data."""

import json
import logging

import redis.asyncio as aioredis

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

redis_client = None


async def get_redis():
    """Get or create the global Redis connection."""
    global redis_client
    if redis_client is None:
        try:
            redis_client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            return None
    return redis_client


async def cache_get(key: str):
    """Get a cached value by key. Returns the deserialized value or None."""
    r = await get_redis()
    if r is None:
        return None
    try:
        val = await r.get(key)
        return json.loads(val) if val else None
    except Exception as e:
        logger.warning(f"Cache get failed for key '{key}': {e}")
        return None


async def cache_set(key: str, value, ttl: int = 300):
    """Set a cached value with TTL (default 300 seconds)."""
    r = await get_redis()
    if r is None:
        return
    try:
        await r.setex(key, ttl, json.dumps(value, default=str))
    except Exception as e:
        logger.warning(f"Cache set failed for key '{key}': {e}")


async def cache_delete(key: str):
    """Delete a single cache key."""
    r = await get_redis()
    if r is None:
        return
    try:
        await r.delete(key)
    except Exception as e:
        logger.warning(f"Cache delete failed for key '{key}': {e}")


async def cache_delete_pattern(pattern: str):
    """Delete all cache keys matching a glob pattern."""
    r = await get_redis()
    if r is None:
        return
    try:
        keys = await r.keys(pattern)
        if keys:
            await r.delete(*keys)
    except Exception as e:
        logger.warning(f"Cache delete pattern failed for '{pattern}': {e}")
