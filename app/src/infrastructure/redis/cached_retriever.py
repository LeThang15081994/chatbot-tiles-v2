"""
Cached Retriever - Wraps LangChain Retriever with Context Cache

This ensures:
- Context cache is checked BEFORE retriever execution
- If cache HIT: skip retriever, skip embedding, skip Milvus
- If cache MISS: execute retriever, then cache result

Architecture:
User Query
  → ContextCache.get()
    ├─> HIT: Return cached documents (skip everything)
    └─> MISS: Continue
         → Retriever.invoke(query)
             → CacheBackedEmbeddings (checks embedding cache)
                 → ONNXEmbeddings (only on embedding cache MISS)
                     → requests.post("/embed")
             → Milvus similarity search
         → ContextCache.set() (cache result)
"""
import logging
from typing import List, Optional, Dict, Any
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from app.src.infrastructure.redis import ContextCache

logger = logging.getLogger(__name__)


class CachedRetriever(BaseRetriever):
    """
    Cached Retriever - Wraps a BaseRetriever with Context Cache

    This is the ONLY place that should trigger embedding calls.
    Embedding is triggered inside the wrapped retriever, which uses
    CacheBackedEmbeddings, which calls ONNXEmbeddings.

    Architecture:
    CachedRetriever
      ↓ (cache check)
      ContextCache
      ↓ (if MISS)
      BaseRetriever.invoke()
        ↓
      CacheBackedEmbeddings
        ↓
      ONNXEmbeddings
        ↓
      requests.post("/embed")
    """

    def __init__(
        self,
        retriever: BaseRetriever,
        context_cache: ContextCache,
        k: int = 5,
        collection: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize cached retriever

        Args:
            retriever: Base retriever to wrap
            context_cache: Context cache instance
            k: Number of documents to retrieve
            collection: Collection name (for cache key)
            filters: Metadata filters (for cache key)
        """
        super().__init__()
        self.retriever = retriever
        self.context_cache = context_cache
        self.k = k
        self.collection = collection
        self.filters = filters

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager=None
    ) -> List[Document]:
        """
        Get relevant documents with context caching

        This is the ONLY method that should trigger embedding.
        Embedding is triggered inside self.retriever.invoke().

        Args:
            query: Search query
            run_manager: Optional callback manager

        Returns:
            List of relevant documents
        """
        # Check context cache FIRST
        cached_docs = self.context_cache.get(
            query=query,
            k=self.k,
            collection=self.collection,
            filters=self.filters
        )

        if cached_docs:
            logger.info(f"Context cache HIT - skipping retriever/embedding/Milvus for: {query[:50]}...")
            return cached_docs

        # Cache MISS - execute retriever
        # This will trigger embedding (via CacheBackedEmbeddings)
        logger.info(f"Context cache MISS - executing retriever for: {query[:50]}...")
        documents = self.retriever.invoke(query, config={"callbacks": run_manager})

        # Cache the result
        self.context_cache.set(
            query=query,
            documents=documents,
            k=self.k,
            collection=self.collection,
            filters=self.filters
        )

        return documents

    async def _aget_relevant_documents(
        self,
        query: str,
        *,
        run_manager=None
    ) -> List[Document]:
        """
        Async version of _get_relevant_documents

        Note: Context cache operations are sync, but retriever may be async
        """
        # Check context cache FIRST
        cached_docs = self.context_cache.get(
            query=query,
            k=self.k,
            collection=self.collection,
            filters=self.filters
        )

        if cached_docs:
            logger.info(f"Context cache HIT - skipping retriever/embedding/Milvus for: {query[:50]}...")
            return cached_docs

        # Cache MISS - execute retriever (async)
        if hasattr(self.retriever, 'ainvoke'):
            documents = await self.retriever.ainvoke(query, config={"callbacks": run_manager})
        else:
            documents = self.retriever.invoke(query, config={"callbacks": run_manager})

        # Cache the result
        self.context_cache.set(
            query=query,
            documents=documents,
            k=self.k,
            collection=self.collection,
            filters=self.filters
        )

        return documents

