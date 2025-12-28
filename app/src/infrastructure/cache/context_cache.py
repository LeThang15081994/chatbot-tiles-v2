"""
Context Cache - Caches Retriever Results

This caches the RESULT of Retriever.invoke(query), not embeddings.
If context cache HIT:
- DO NOT call retriever
- DO NOT call embedding
- DO NOT call Milvus

Cache key includes:
- Normalized query
- Retriever config (k, filters, collection)
- Embedding version (to invalidate on model change)

Architecture:
User Query
  → Context Cache Check
    ├─> HIT: Return cached documents (skip retriever/embedding/Milvus)
    └─> MISS: Continue to Retriever
         → Cache result before returning
"""
import json
import hashlib
import logging
from typing import List, Optional, Dict, Any
from langchain_core.documents import Document

from app.src.infrastructure.config.settings import RedisSettings, EmbeddingSettings

logger = logging.getLogger(__name__)


class ContextCache:
    """
    Context Cache for Retriever Results

    Caches the output of Retriever.invoke(query) to avoid:
    - Duplicate embedding calls
    - Duplicate Milvus queries
    - Duplicate retriever execution

    This is separate from embedding cache:
    - Embedding cache: caches embedding vectors
    - Context cache: caches retriever results (documents)
    """

    def __init__(
        self,
        redis_settings: RedisSettings,
        embedding_settings: EmbeddingSettings,
        cache_ttl: int = 3600  # 1 hour default
    ):
        """
        Initialize context cache

        Args:
            redis_settings: Redis configuration
            embedding_settings: Embedding configuration (for versioning)
            cache_ttl: Cache TTL in seconds
        """
        import redis

        self.redis_client = redis.Redis(
            host=redis_settings.REDIS_HOST,
            port=redis_settings.REDIS_PORT,
            password=redis_settings.REDIS_PASSWORD,
            decode_responses=False  # Store as bytes for JSON
        )

        self.embedding_version = f"{embedding_settings.EMBEDDING_MODEL}:{embedding_settings.EMBEDDING_DIMENSION}"
        self.cache_ttl = cache_ttl
        self.cache_prefix = "context_cache"

    def _normalize_query(self, query: str) -> str:
        """Normalize query for consistent caching"""
        return query.strip().lower()

    def _build_cache_key(
        self,
        query: str,
        k: int = 5,
        collection: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build cache key from query + retriever config

        Args:
            query: User query
            k: Number of documents to retrieve
            collection: Collection name (if specified)
            filters: Metadata filters (if any)

        Returns:
            Cache key string
        """
        normalized_query = self._normalize_query(query)

        # Build config hash
        config = {
            "k": k,
            "collection": collection,
            "filters": filters or {},
            "embedding_version": self.embedding_version
        }
        config_str = json.dumps(config, sort_keys=True)
        config_hash = hashlib.md5(config_str.encode()).hexdigest()[:8]

        # Cache key: context_cache:{query_hash}:{config_hash}
        query_hash = hashlib.md5(normalized_query.encode()).hexdigest()[:8]
        return f"{self.cache_prefix}:{query_hash}:{config_hash}"

    def get(
        self,
        query: str,
        k: int = 5,
        collection: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Optional[List[Document]]:
        """
        Get cached retriever results

        Args:
            query: User query
            k: Number of documents
            collection: Collection name
            filters: Metadata filters

        Returns:
            Cached documents if found, None otherwise
        """
        try:
            cache_key = self._build_cache_key(query, k, collection, filters)
            cached_data = self.redis_client.get(cache_key)

            if cached_data:
                # Deserialize documents
                data = json.loads(cached_data.decode('utf-8'))
                documents = [
                    Document(
                        page_content=doc["page_content"],
                        metadata=doc.get("metadata", {})
                    )
                    for doc in data["documents"]
                ]
                logger.info(f"Context cache HIT for query: {query[:50]}...")
                return documents

            logger.info(f"Context cache MISS for query: {query[:50]}...")
            return None

        except Exception as e:
            logger.warning(f"Context cache lookup error: {e}")
            return None

    def set(
        self,
        query: str,
        documents: List[Document],
        k: int = 5,
        collection: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Cache retriever results

        Args:
            query: User query
            documents: Documents to cache
            k: Number of documents
            collection: Collection name
            filters: Metadata filters

        Returns:
            True if successful
        """
        try:
            cache_key = self._build_cache_key(query, k, collection, filters)

            # Serialize documents
            data = {
                "documents": [
                    {
                        "page_content": doc.page_content,
                        "metadata": doc.metadata
                    }
                    for doc in documents
                ]
            }

            # Store in Redis
            self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(data)
            )

            logger.info(f"Context cache STORED for query: {query[:50]}...")
            return True

        except Exception as e:
            logger.error(f"Failed to store in context cache: {e}")
            return False

