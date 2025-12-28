"""
Vector Store Repository Interface
Abstract interface for vector database repository
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from app.src.application.dto.search_dto import SearchResultDTO


class IVectorStoreRepository(ABC):
    """
    Interface for vector store repository

    Application layer interface - no infrastructure dependencies.
    Allows Application layer to perform vector searches without depending on concrete implementations.
    """

    @abstractmethod
    async def hybrid_search(
        self,
        query: str,
        k: int = 5,
        collection_name: Optional[str] = None,
        filter_expr: Optional[str] = None
    ) -> List[SearchResultDTO]:
        """
        Perform hybrid search (vector + BM25)

        Args:
            query: Search query
            k: Number of results
            collection_name: Optional collection name
            filter_expr: Optional filter expression

        Returns:
            List of search results with hybrid scores
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check vector store health

        Returns:
            True if healthy, False otherwise
        """
        pass

