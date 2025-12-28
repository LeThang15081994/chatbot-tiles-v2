"""
Text Cache Interface (Cache #1)
Exact text answer cache using KV storage
"""
from abc import ABC, abstractmethod
from typing import Optional


class ITextCache(ABC):
    """
    Interface for exact text answer cache (Cache #1)

    Key: answer:text:{hash(normalized_text)}
    Purpose: Fast exact match for identical queries
    """

    @abstractmethod
    async def get(self, text_hash: str) -> Optional[str]:
        """
        Get cached answer by text hash

        Args:
            text_hash: Hash of normalized text

        Returns:
            Cached answer if found, None otherwise
        """
        pass

    @abstractmethod
    async def set(self, text_hash: str, answer: str, ttl: Optional[int] = None) -> bool:
        """
        Cache answer by text hash

        Args:
            text_hash: Hash of normalized text
            answer: Answer to cache
            ttl: Optional TTL in seconds

        Returns:
            True if successful
        """
        pass

