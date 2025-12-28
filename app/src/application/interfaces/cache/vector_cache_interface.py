"""
Vector Cache Interface (Cache #3)
Exact embedding answer cache using KV storage
"""
from abc import ABC, abstractmethod
from typing import Optional, List


class IVectorCache(ABC):
    """
    Interface for exact embedding answer cache (Cache #3)

    Key: answer:emb:{hash(query_vector)}
    Purpose: Fast exact match for identical embeddings
    """

    @abstractmethod
    async def get(self, vector_hash: str) -> Optional[str]:
        """
        Get cached answer by vector hash

        Args:
            vector_hash: Hash of query vector

        Returns:
            Cached answer if found, None otherwise
        """
        pass

    @abstractmethod
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
        pass

