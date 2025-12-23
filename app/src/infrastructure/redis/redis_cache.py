"""
Redis Cache Repository Implementation
"""
from typing import Optional, Any
import json
import redis.asyncio as aioredis

from app.src.application.interfaces.cache_repository import ICacheRepository
from app.src.infrastructure.config.redis_settings import RedisSettings


class RedisCacheRepository(ICacheRepository):
    """
    Redis implementation of ICache

    Provides caching with TTL support for RAG responses
    """

    def __init__(self, settings: RedisSettings):
        """
        Initialize Redis cache

        Args:
            settings: Redis configuration settings
        """
        self.settings = settings
        self.client: Optional[aioredis.Redis] = None
        self._connect()

    def _connect(self) -> None:
        """Establish Redis connection"""
        try:
            self.client = aioredis.from_url(
                f"redis://{self.settings.REDIS_HOST}:{self.settings.REDIS_PORT}",
                encoding="utf-8",
                decode_responses=True
            )
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Redis: {e}")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            if not self.client:
                return None

            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None

        except Exception:
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache with optional TTL"""
        try:
            if not self.client:
                return False

            serialized = json.dumps(value, ensure_ascii=False)

            if ttl:
                await self.client.setex(key, ttl, serialized)
            else:
                await self.client.set(key, serialized)

            return True

        except Exception:
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            if not self.client:
                return False

            await self.client.delete(key)
            return True

        except Exception:
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            if not self.client:
                return False
            return await self.client.exists(key) > 0
        except Exception:
            return False

    async def clear(self, pattern: Optional[str] = None) -> int:
        """Clear cache entries matching pattern"""
        try:
            if not self.client:
                return 0

            if pattern:
                keys = await self.client.keys(pattern)
            else:
                keys = await self.client.keys("*")

            if keys:
                await self.client.delete(*keys)
                return len(keys)
            return 0
        except Exception:
            return 0

    async def get_ttl(self, key: str) -> Optional[int]:
        """Get remaining TTL for a key"""
        try:
            if not self.client:
                return None
            ttl = await self.client.ttl(key)
            return ttl if ttl >= 0 else None
        except Exception:
            return None

    async def health_check(self) -> bool:
        """Check Redis health"""
        try:
            if not self.client:
                return False

            await self.client.ping()
            return True

        except Exception:
            return False

    async def get_stats(self) -> dict:
        """Get cache statistics"""
        try:
            if not self.client:
                return {}

            info = await self.client.info("stats")
            return {
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_keys": len(await self.client.keys("*"))
            }
        except Exception:
            return {}

