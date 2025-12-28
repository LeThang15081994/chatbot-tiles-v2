"""
Redis Vector Cache Implementation (Cache #3)
Exact embedding answer cache using KV storage
"""
import json
import redis
from typing import Optional
import asyncio
from app.src.application.interfaces.cache.vector_cache_interface import IVectorCache
from app.src.infrastructure.config.settings import RedisSettings


class RedisVectorCache(IVectorCache):
    """
    Redis implementation of IVectorCache (Cache #3)

    Key format: answer:emb:{hash}
    Uses Redis DB 0
    """

    def __init__(self, redis_settings: RedisSettings, default_ttl: int = 900):
        """
        Initialize Redis vector cache

        Args:
            redis_settings: Redis configuration
            default_ttl: Default TTL in seconds (15 minutes)
        """
        self.redis_client = None
        self.redis_settings = redis_settings
        self.default_ttl = default_ttl
        self.key_prefix = "answer:emb:"
        self._connect()

    def _connect(self) -> None:
        """Connect to Redis"""
        self.redis_client = redis.Redis(
            host=self.redis_settings.REDIS_HOST,
            port=self.redis_settings.REDIS_PORT,
            db=0,  # Use DB 0 only
            password=self.redis_settings.REDIS_PASSWORD if self.redis_settings.REDIS_PASSWORD else None,
            decode_responses=True
        )

    async def get(self, vector_hash: str) -> Optional[str]:
        """
        Get cached answer by vector hash

        Args:
            vector_hash: Hash of query vector

        Returns:
            Cached answer if found, None otherwise
        """
        try:
            key = f"{self.key_prefix}{vector_hash}"
            cached = await asyncio.to_thread(self.redis_client.get, key)
            if cached:
                return json.loads(cached)
            return None
        except Exception as e:
            print(f"Redis vector cache get error: {e}")
            return None

    async def set(self, vector_hash: str, answer: str, ttl: Optional[int] = None) -> bool:
        """
        Cache answer by vector hash

        Args:
            vector_hash: Hash of query vector
            answer: Answer to cache
            ttl: Optional TTL in seconds

        Returns:
            True if successful
        """
        try:
            key = f"{self.key_prefix}{vector_hash}"
            ttl = ttl or self.default_ttl
            await asyncio.to_thread(
                self.redis_client.setex,
                key,
                ttl,
                json.dumps(answer)
            )
            return True
        except Exception as e:
            print(f"Redis vector cache set error: {e}")
            return False

