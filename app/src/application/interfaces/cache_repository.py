"""
Cache Repository Interface
"""
from abc import ABC, abstractmethod
from typing import Optional, Any, Dict


class ICacheRepository(ABC):
    """
    Interface for cache operations
    Abstracts the underlying cache implementation (Redis, Memcached, etc.)
    """

    @abstractmethod
    async def get(
        self,
        key: str
    ) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value if exists, None otherwise
        """
        pass

    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None for no expiration)

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    async def delete(
        self,
        key: str
    ) -> bool:
        """
        Delete value from cache

        Args:
            key: Cache key

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    async def exists(
        self,
        key: str
    ) -> bool:
        """
        Check if key exists in cache

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        pass

    @abstractmethod
    async def clear(
        self,
        pattern: Optional[str] = None
    ) -> int:
        """
        Clear cache entries matching pattern

        Args:
            pattern: Pattern to match (e.g., "user:*"). If None, clears all.

        Returns:
            Number of keys deleted
        """
        pass

    @abstractmethod
    async def get_ttl(
        self,
        key: str
    ) -> Optional[int]:
        """
        Get remaining TTL for a key

        Args:
            key: Cache key

        Returns:
            TTL in seconds, None if key doesn't exist or has no expiration
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if cache service is healthy and accessible

        Returns:
            True if healthy
        """
        pass

    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache stats (hits, misses, size, etc.)
        """
        pass


class ISemanticCacheRepository(ICacheRepository):
    """
    Interface for semantic cache operations
    Extends basic cache with semantic similarity
    """

    @abstractmethod
    async def get_similar(
        self,
        query: str,
        threshold: float = 0.95
    ) -> Optional[Any]:
        """
        Get cached value for semantically similar query

        Args:
            query: Query text
            threshold: Similarity threshold (0.0 to 1.0)

        Returns:
            Cached value if similar query exists, None otherwise
        """
        pass

    @abstractmethod
    async def set_with_embedding(
        self,
        query: str,
        value: Any,
        embedding: Optional[list] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache with query embedding for semantic matching

        Args:
            query: Query text
            value: Value to cache
            embedding: Pre-computed embedding (computed if None)
            ttl: Time to live in seconds

        Returns:
            True if successful
        """
        pass

