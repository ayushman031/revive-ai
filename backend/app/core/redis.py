"""Redis client configuration without eager network connections."""

from functools import lru_cache

from redis import Redis

from app.core.config import get_settings


@lru_cache
def get_redis_client() -> Redis:
    """Create the configured Redis client on first use."""
    return Redis.from_url(get_settings().redis_url, decode_responses=True)
