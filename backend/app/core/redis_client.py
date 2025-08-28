"""Redis client configuration."""

import json
import logging
from typing import Any, Optional

from app.core.config import settings
from redis.asyncio import Redis
from redis.exceptions import ConnectionError, TimeoutError

logger = logging.getLogger(__name__)

# Global Redis client
redis_client: Optional[Redis] = None


async def init_redis():
    """Initialize Redis connection."""
    global redis_client
    try:
        redis_client = Redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_timeout=settings.REDIS_TIMEOUT,
            socket_connect_timeout=settings.REDIS_TIMEOUT,
            retry_on_timeout=True,
        )

        # Test connection
        await redis_client.ping()
        logger.info("Redis connection established successfully")

    except (ConnectionError, TimeoutError) as e:
        logger.error(f"Failed to connect to Redis: {e}")
        redis_client = None
        raise


async def get_redis() -> Redis:
    """Get Redis client instance."""
    if redis_client is None:
        raise ConnectionError("Redis client not initialized")
    return redis_client


async def set_cache(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """Set a value in Redis cache."""
    try:
        client = await get_redis()
        serialized_value = json.dumps(
            value) if not isinstance(value, str) else value
        cache_ttl = ttl or settings.REDIS_DEFAULT_TTL
        await client.setex(key, cache_ttl, serialized_value)
        return True
    except Exception as e:
        logger.error(f"Failed to set cache for key {key}: {e}")
        return False


async def get_cache(key: str) -> Optional[Any]:
    """Get a value from Redis cache."""
    try:
        client = await get_redis()
        value = await client.get(key)
        if value is None:
            return None

        # Try to deserialize JSON, fallback to string
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    except Exception as e:
        logger.error(f"Failed to get cache for key {key}: {e}")
        return None


async def delete_cache(key: str) -> bool:
    """Delete a key from Redis cache."""
    try:
        client = await get_redis()
        await client.delete(key)
        return True
    except Exception as e:
        logger.error(f"Failed to delete cache for key {key}: {e}")
        return False


async def check_redis_health() -> str:
    """Check Redis connectivity for health checks."""
    try:
        client = await get_redis()
        await client.ping()
        return "ok"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return "error"
