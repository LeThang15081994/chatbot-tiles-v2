"""
LangChain Retriever Factory
Creates LangChain Retrievers from Milvus VectorStore
"""
from typing import Optional, Dict, Any
from langchain_core.retrievers import BaseRetriever
from langchain_milvus import Milvus
from langchain_core.documents import Document
from langchain_core.callbacks import CallbackManagerForRetrieverRun

from app.src.infrastructure.vectordb.milvus_repository import MilvusVectorStoreRepository


class MilvusLangChainRetriever(BaseRetriever):
    """
    LangChain Retriever implementation using Milvus VectorStore

    This is a pure LangChain Retriever that wraps Milvus VectorStore
    and can be used with LangChain chains, agents, and tools.
    """

    def __init__(
        self,
        vector_store: Milvus,
        k: int = 5,
        search_kwargs: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Milvus LangChain Retriever

        Args:
            vector_store: LangChain Milvus VectorStore instance
            k: Number of documents to retrieve
            search_kwargs: Additional search parameters (e.g., expr for filters)
        """
        super().__init__()
        object.__setattr__(self, 'vector_store', vector_store)
        object.__setattr__(self, 'k', k)
        object.__setattr__(self, 'search_kwargs', search_kwargs or {})

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun
    ) -> list[Document]:
        """
        Get relevant documents using vector similarity search

        Args:
            query: Search query text
            run_manager: Callback manager for retriever run

        Returns:
            List of relevant documents
        """
        try:
            # Use vector_store similarity_search
            documents = self.vector_store.similarity_search(
                query=query,
                k=self.k,
                **self.search_kwargs
            )
            return documents
        except Exception as e:
            raise RuntimeError(f"Retrieval failed: {e}")

    async def _aget_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun
    ) -> list[Document]:
        """
        Async version of _get_relevant_documents

        Args:
            query: Search query text
            run_manager: Callback manager for retriever run

        Returns:
            List of relevant documents
        """
        try:
            # Use vector_store similarity_search (sync, but wrapped in async)
            documents = self.vector_store.similarity_search(
                query=query,
                k=self.k,
                **self.search_kwargs
            )
            return documents
        except Exception as e:
            raise RuntimeError(f"Async retrieval failed: {e}")


class LangChainRetrieverFactory:
    """
    Factory for creating LangChain Retrievers from Milvus repository
    """

    @staticmethod
    def create_retriever(
        milvus_repository: MilvusVectorStoreRepository,
        collection_name: Optional[str] = None,
        k: int = 5,
        filter_expr: Optional[str] = None
    ) -> BaseRetriever:
        """
        Create LangChain Retriever from Milvus repository

        Args:
            milvus_repository: Milvus repository instance
            collection_name: Collection name (company_document_info, products, etc.)
            k: Number of documents to retrieve
            filter_expr: Optional filter expression for metadata filtering

        Returns:
            LangChain BaseRetriever instance
        """
        # Get the appropriate LangChain Milvus VectorStore
        _, wrapper, _ = milvus_repository._get_collection_by_name(collection_name)

        if not wrapper:
            raise ValueError(f"Collection not found: {collection_name}")

        # Build search kwargs
        search_kwargs = {}
        if filter_expr:
            search_kwargs["expr"] = filter_expr

        # For products collection, always filter active products
        if collection_name and "product" in collection_name.lower():
            active_filter = "isActive == true"
            if filter_expr:
                search_kwargs["expr"] = f"{filter_expr} && {active_filter}"
            else:
                search_kwargs["expr"] = active_filter

        # Create retriever
        retriever = MilvusLangChainRetriever(
            vector_store=wrapper,
            k=k,
            search_kwargs=search_kwargs
        )

        return retriever

    @staticmethod
    def create_retrievers_for_all_collections(
        milvus_repository: MilvusVectorStoreRepository,
        k: int = 5
    ) -> Dict[str, BaseRetriever]:
        """
        Create retrievers for all available collections

        Args:
            milvus_repository: Milvus repository instance
            k: Number of documents to retrieve

        Returns:
            Dictionary mapping collection names to retrievers
        """
        retrievers = {}

        # Company document retriever
        if milvus_repository.langchain_milvus_document:
            retrievers["company_document_info"] = MilvusLangChainRetriever(
                vector_store=milvus_repository.langchain_milvus_document,
                k=k
            )

        # Products retriever
        if milvus_repository.langchain_milvus_products:
            retrievers["products"] = MilvusLangChainRetriever(
                vector_store=milvus_repository.langchain_milvus_products,
                k=k,
                search_kwargs={"expr": "isActive == true"}
            )

        # Products info retriever
        if milvus_repository.langchain_milvus_products_info:
            retrievers["products_info"] = MilvusLangChainRetriever(
                vector_store=milvus_repository.langchain_milvus_products_info,
                k=k
            )

        # Collection info retriever
        if milvus_repository.langchain_milvus_collection_info:
            retrievers["collection_info"] = MilvusLangChainRetriever(
                vector_store=milvus_repository.langchain_milvus_collection_info,
                k=k
            )

        return retrievers

