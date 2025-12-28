"""
Retriever Factory Interface
Abstract interface for creating retrievers
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from langchain_core.retrievers import BaseRetriever


class IRetrieverFactory(ABC):
    """
    Interface for retriever factory

    Application layer interface - no infrastructure dependencies.
    Allows Application layer to create retrievers without depending on concrete implementations.
    """

    @abstractmethod
    def create_retriever(
        self,
        vector_store_repository: Any,  # IVectorStoreRepository (using Any to avoid circular import)
        collection_name: Optional[str] = None,
        k: int = 5,
        filter_expr: Optional[str] = None
    ) -> BaseRetriever:
        """
        Create retriever from vector store repository

        Args:
            vector_store_repository: Vector store repository instance
            collection_name: Collection name
            k: Number of documents to retrieve
            filter_expr: Optional filter expression

        Returns:
            LangChain BaseRetriever instance
        """
        pass

    @abstractmethod
    def create_retrievers_for_all_collections(
        self,
        vector_store_repository: Any,  # IVectorStoreRepository
        k: int = 5
    ) -> Dict[str, BaseRetriever]:
        """
        Create retrievers for all available collections

        Args:
            vector_store_repository: Vector store repository instance
            k: Number of documents to retrieve

        Returns:
            Dictionary mapping collection names to retrievers
        """
        pass

