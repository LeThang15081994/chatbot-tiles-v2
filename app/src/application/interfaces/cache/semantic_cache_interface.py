"""
Semantic Cache Interface (Cache #4)
HNSW semantic search for similar queries
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Tuple


class ISemanticCache(ABC):
    """
    Interface for semantic cache (Cache #4)

    Index: idx:answer:semantic (HNSW)
    Purpose: KNN search for semantically similar queries
    """

    @abstractmethod
    async def search(
        self,
        query_vector: List[float],
        similarity_threshold: float = 0.8,
        top_k: int = 1
    ) -> Optional[Tuple[str, float]]:
        """
        Search for semantically similar cached answer

        Args:
            query_vector: Query embedding vector
            similarity_threshold: Minimum similarity score
            top_k: Number of results to return

        Returns:
            Tuple of (answer, similarity_score) if found, None otherwise
        """
        pass

    @abstractmethod
    async def add(
        self,
        query_vector: List[float],
        answer: str,
        answer_id: Optional[str] = None
    ) -> bool:
        """
        Add answer to semantic cache

        Args:
            query_vector: Query embedding vector
            answer: Answer to cache
            answer_id: Optional answer ID

        Returns:
            True if successful
        """
        pass

