"""
Vector Store Repository Interface
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from ..dto.document_dto import DocumentDTO
from ..dto.search_dto import SearchResultDTO


class IVectorStoreRepository(ABC):
    """
    Interface for vector store operations
    Abstracts the underlying vector database implementation (Milvus, Pinecone, etc.)
    """

    @abstractmethod
    async def search(
        self,
        query: str,
        k: int = 5,
        collection_name: Optional[str] = None,
        filter_expr: Optional[str] = None
    ) -> List[SearchResultDTO]:
        """
        Perform vector similarity search

        Args:
            query: Search query text
            k: Number of results to return
            collection_name: Name of collection to search
            filter_expr: Filter expression for metadata filtering

        Returns:
            List of search results
        """
        pass

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
            query: Search query text
            k: Number of results to return
            collection_name: Name of collection to search
            filter_expr: Filter expression for metadata filtering

        Returns:
            List of search results
        """
        pass

    @abstractmethod
    async def add_documents(
        self,
        documents: List[DocumentDTO],
        collection_name: Optional[str] = None
    ) -> List[str]:
        """
        Add documents to vector store

        Args:
            documents: List of documents to add
            collection_name: Name of collection to add to

        Returns:
            List of document IDs
        """
        pass

    @abstractmethod
    async def update_document(
        self,
        document_id: str,
        document: DocumentDTO,
        collection_name: Optional[str] = None
    ) -> bool:
        """
        Update a document in vector store

        Args:
            document_id: ID of document to update
            document: Updated document data
            collection_name: Name of collection

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    async def delete_documents(
        self,
        document_ids: List[str],
        collection_name: Optional[str] = None
    ) -> bool:
        """
        Delete documents from vector store

        Args:
            document_ids: List of document IDs to delete
            collection_name: Name of collection

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    async def get_document(
        self,
        document_id: str,
        collection_name: Optional[str] = None
    ) -> Optional[DocumentDTO]:
        """
        Get a document by ID

        Args:
            document_id: Document ID
            collection_name: Name of collection

        Returns:
            Document if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_collection_stats(
        self,
        collection_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get collection statistics

        Args:
            collection_name: Name of collection

        Returns:
            Dictionary with collection stats
        """
        pass

    @abstractmethod
    async def list_collections(self) -> List[str]:
        """
        List all available collections

        Returns:
            List of collection names
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if vector store is healthy and accessible

        Returns:
            True if healthy
        """
        pass

