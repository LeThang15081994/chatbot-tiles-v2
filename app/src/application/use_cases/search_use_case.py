"""
Search Use Case - Using LangChain Retriever
"""
import time
from typing import List, Optional, Dict, Any
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document

from app.src.application.dto.search_dto import (
    SearchRequestDTO,
    SearchResponseDTO,
    SearchResultDTO,
    SearchMetadataDTO,
    CollectionType
)
from app.src.application.interfaces.repositories.vector_store_interface import IVectorStoreRepository
from app.src.application.interfaces.repositories.retriever_factory_interface import IRetrieverFactory


class SearchUseCase:
    """
    Use case for document search functionality using LangChain Retriever

    Responsibilities:
    - Execute searches using LangChain Retrievers
    - Handle different collections
    - Format and return search results
    """

    def __init__(
        self,
        vector_store_repository: IVectorStoreRepository,
        retriever_factory: Optional[IRetrieverFactory] = None,
        retrievers: Optional[Dict[str, BaseRetriever]] = None
    ):
        """
        Initialize search use case

        Args:
            vector_store_repository: Vector store repository (IVectorStoreRepository interface)
            retriever_factory: Optional retriever factory (IRetrieverFactory interface)
            retrievers: Optional pre-created retrievers dict (for performance)
        """
        self.vector_store_repository = vector_store_repository
        self.retriever_factory = retriever_factory
        self._retrievers_cache = retrievers or {}

    def _get_retriever(
        self,
        collection_name: Optional[str],
        filter_expr: Optional[str] = None,
        k: int = 5
    ) -> BaseRetriever:
        """
        Get or create LangChain Retriever for collection

        Args:
            collection_name: Collection name
            filter_expr: Optional filter expression
            k: Number of documents to retrieve

        Returns:
            LangChain BaseRetriever instance
        """
        # Create cache key
        cache_key = f"{collection_name}:{filter_expr}:{k}"

        # Check cache
        if cache_key in self._retrievers_cache:
            return self._retrievers_cache[cache_key]

        # Create new retriever using factory
        if not self.retriever_factory:
            raise RuntimeError("RetrieverFactory is required but not provided")

        retriever = self.retriever_factory.create_retriever(
            vector_store_repository=self.vector_store_repository,
            collection_name=collection_name,
            k=k,
            filter_expr=filter_expr
        )

        # Cache it
        self._retrievers_cache[cache_key] = retriever

        return retriever

    def _convert_langchain_doc_to_dto(
        self,
        doc: Document,
        collection_name: Optional[str]
    ) -> SearchResultDTO:
        """
        Convert LangChain Document to SearchResultDTO

        Args:
            doc: LangChain Document
            collection_name: Collection name

        Returns:
            SearchResultDTO
        """
        metadata = doc.metadata

        search_metadata = SearchMetadataDTO(
            id=metadata.get('id'),
            category=metadata.get('category'),
            source=metadata.get('source'),
            brand_name=metadata.get('brand_name') or metadata.get('brandName'),
            collection_name=collection_name,
            updated_time=metadata.get('updated_time') or metadata.get('updatedTime'),
            vector_score=metadata.get('score') or metadata.get('vector_score')
        )

        return SearchResultDTO(
            content=doc.page_content,
            metadata=search_metadata,
            score=metadata.get('score') or metadata.get('vector_score') or 0.0
        )

    async def search_documents(
        self,
        request: SearchRequestDTO
    ) -> SearchResponseDTO:
        """
        Search documents using LangChain Retriever

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

        # Get LangChain Retriever
        retriever = self._get_retriever(
            collection_name=collection_name,
            filter_expr=filter_expr,
            k=request.top_k
        )

        # Execute retrieval using LangChain Retriever
        documents = retriever.invoke(request.query)

        # Convert LangChain Documents to SearchResultDTO
        results = [
            self._convert_langchain_doc_to_dto(doc, collection_name)
            for doc in documents
        ]

        processing_time = int((time.time() - start_time) * 1000)

        return SearchResponseDTO(
            results=results,
            query=request.query,
            collection_name=collection_name or "auto",
            total_results=len(results),
            search_type="vector",  # LangChain Retriever uses vector similarity
            processing_time_ms=processing_time
        )

    async def vector_search(
        self,
        query: str,
        k: int = 5,
        collection_name: Optional[str] = None
    ) -> List[SearchResultDTO]:
        """
        Perform vector similarity search using LangChain Retriever

        Args:
            query: Search query
            k: Number of results
            collection_name: Optional collection name

        Returns:
            List of search results
        """
        # Get retriever
        retriever = self._get_retriever(
            collection_name=collection_name,
            k=k
        )

        # Execute retrieval
        documents = retriever.invoke(query)

        # Convert to DTOs
        return [
            self._convert_langchain_doc_to_dto(doc, collection_name)
            for doc in documents
        ]

    async def hybrid_search(
        self,
        query: str,
        k: int = 5,
        collection_name: Optional[str] = None,
        filter_expr: Optional[str] = None
    ) -> List[SearchResultDTO]:
        """
        Perform hybrid search (vector + BM25) using Milvus repository

        This method uses:
        - LangChain wrapper for vector similarity search (70% weight)
        - Direct PyMilvus for BM25 search (30% weight)
        - Combines results with weighted scoring

        Args:
            query: Search query
            k: Number of results
            collection_name: Optional collection name
            filter_expr: Optional filter expression

        Returns:
            List of search results with hybrid scores
        """
        # Use vector store repository's hybrid_search method
        # This uses LangChain for vector search and direct PyMilvus for BM25
        return await self.vector_store_repository.hybrid_search(
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

