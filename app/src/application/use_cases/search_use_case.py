"""
Search Use Case
"""
import time
from typing import List, Optional
from ..interfaces.vector_store_repository import IVectorStoreRepository
from ..dto.search_dto import (
    SearchRequestDTO,
    SearchResponseDTO,
    SearchResultDTO,
    CollectionType
)


class SearchUseCase:
    """
    Use case for document search functionality

    Responsibilities:
    - Execute searches across vector store collections
    - Handle different search types (vector, BM25, hybrid)
    - Format and return search results
    """

    def __init__(
        self,
        vector_store: IVectorStoreRepository
    ):
        """
        Initialize search use case

        Args:
            vector_store: Vector store repository
        """
        self.vector_store = vector_store

    async def search_documents(
        self,
        request: SearchRequestDTO
    ) -> SearchResponseDTO:
        """
        Search documents in vector store

        Args:
            request: Search request DTO

        Returns:
            Search response DTO with results
        """
        start_time = time.time()

        # Determine collection name
        collection_name = self._determine_collection(
            request.collection_name,
            request.query
        )

        # Build filter expression from metadata filter
        filter_expr = self._build_filter_expression(
            request.metadata_filter,
            collection_name
        )

        # Execute hybrid search
        results = await self.vector_store.hybrid_search(
            query=request.query,
            k=request.top_k,
            collection_name=collection_name,
            filter_expr=filter_expr
        )

        processing_time = int((time.time() - start_time) * 1000)

        return SearchResponseDTO(
            results=results,
            query=request.query,
            collection_name=collection_name or "auto",
            total_results=len(results),
            processing_time_ms=processing_time
        )

    async def vector_search(
        self,
        query: str,
        k: int = 5,
        collection_name: Optional[str] = None
    ) -> List[SearchResultDTO]:
        """
        Perform vector similarity search only

        Args:
            query: Search query
            k: Number of results
            collection_name: Optional collection name

        Returns:
            List of search results
        """
        return await self.vector_store.search(
            query=query,
            k=k,
            collection_name=collection_name
        )

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
            List of search results
        """
        return await self.vector_store.hybrid_search(
            query=query,
            k=k,
            collection_name=collection_name,
            filter_expr=filter_expr
        )

    def _determine_collection(
        self,
        collection_type: Optional[CollectionType],
        query: str
    ) -> Optional[str]:
        """
        Determine which collection to search based on query and type
        Maps CollectionType enum to actual Milvus collection names

        Args:
            collection_type: Requested collection type
            query: Search query

        Returns:
            Collection name (actual Milvus collection name) or None for auto-detect
        """
        if not collection_type or collection_type == CollectionType.AUTO:
            # Auto-detect based on query keywords
            # Simple keyword matching for now
            query_lower = query.lower()

            product_keywords = [
                'gạch', 'tile', 'product', 'wooden', 'porcelain',
                'ceramic', 'price', 'size', 'collection', 'brand'
            ]

            for keyword in product_keywords:
                if keyword in query_lower:
                    return "products"

            # Default to company_document_info (actual collection name)
            return "company_document_info"

        # Map CollectionType enum to actual Milvus collection names
        elif collection_type == CollectionType.COMPANY_DOCUMENT:
            return "company_document_info"  # Map to actual collection name

        elif collection_type == CollectionType.COLLECTION_INFO:
            return "collection_info"

        elif collection_type == CollectionType.PRODUCTS_INFO:
            return "products_info"

        return None

    def _build_filter_expression(
        self,
        metadata_filter: Optional[dict],
        collection_name: Optional[str]
    ) -> Optional[str]:
        """
        Build filter expression from metadata filter dict

        Args:
            metadata_filter: Metadata filter dictionary
            collection_name: Collection name

        Returns:
            Filter expression string
        """
        filter_parts = []

        # Add metadata filters
        if metadata_filter:
            for key, value in metadata_filter.items():
                if isinstance(value, str):
                    filter_parts.append(f"{key} == '{value}'")
                elif isinstance(value, (int, float)):
                    filter_parts.append(f"{key} == {value}")
                elif isinstance(value, list):
                    values_str = "', '".join([str(v) for v in value])
                    filter_parts.append(f"{key} in ['{values_str}']")

        # For products collection, always filter by active status
        if collection_name == "products":
            filter_parts.append("isActive == true")

        return " and ".join(filter_parts) if filter_parts else None

