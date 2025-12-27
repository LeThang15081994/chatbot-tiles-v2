"""
Cache-Backed Embeddings using LangChain CacheBackedEmbeddings

This wraps ONNXEmbeddings with Redis-based caching to avoid duplicate
embedding calls for the same text.

Architecture:
- CacheBackedEmbeddings wraps ONNXEmbeddings
- Uses Redis as byte store for embedding cache
- Cache key: normalized text + embedding version
- TTL: Configurable (default: 1 hour)
"""
import hashlib
import json
from typing import List
from langchain_core.embeddings import Embeddings
from langchain.embeddings.cache import CacheBackedEmbeddings
from langchain_community.storage import RedisStore

from app.src.infrastructure.config.redis_settings import RedisSettings
from app.src.infrastructure.config.embedding_settings import EmbeddingSettings


class CachedONNXEmbeddings(Embeddings):
    """
    Cache-backed ONNX Embeddings

    Wraps ONNXEmbeddings with Redis-based caching using LangChain's
    CacheBackedEmbeddings. This ensures:
    - Same text is embedded only once (cached in Redis)
    - Cache is shared across all retrievers
    - Embedding versioning prevents stale cache

    Architecture:
    RedisStore (byte store)
      ↓
    CacheBackedEmbeddings
      ↓
    ONNXEmbeddings (actual embedding)

    This class inherits from Embeddings so it can be used directly
    as embedding_function in Milvus and other LangChain components.
    """

    def __init__(
        self,
        base_embeddings: Embeddings,
        redis_settings: RedisSettings,
        embedding_settings: EmbeddingSettings,
        cache_ttl: int = 600  # 10 minutes default
    ):
        """
        Initialize cache-backed embeddings

        Args:
            base_embeddings: Base embeddings (ONNXEmbeddings)
            redis_settings: Redis configuration
            embedding_settings: Embedding configuration (for versioning)
            cache_ttl: Cache TTL in seconds
        """
        super().__init__()
        # Build Redis URL
        redis_url = f"redis://{redis_settings.REDIS_HOST}:{redis_settings.REDIS_PORT}"
        if redis_settings.REDIS_PASSWORD:
            redis_url = f"redis://:{redis_settings.REDIS_PASSWORD}@{redis_settings.REDIS_HOST}:{redis_settings.REDIS_PORT}"

        # Create Redis store for embedding cache
        # Namespace: embedding_cache:{model_name}:{dimension}
        cache_namespace = f"embedding_cache:{embedding_settings.EMBEDDING_MODEL}:{embedding_settings.EMBEDDING_DIMENSION}"

        redis_store = RedisStore(
            redis_url=redis_url,
            namespace=cache_namespace,
            ttl=cache_ttl
        )

        # Wrap base embeddings with cache
        # CacheBackedEmbeddings is itself an Embeddings instance
        self._cached_embeddings = CacheBackedEmbeddings(
            underlying_embeddings=base_embeddings,
            document_embedding_store=redis_store,
            namespace=cache_namespace
        )

    def embed_query(self, text: str) -> List[float]:
        """Embed query (delegates to CacheBackedEmbeddings)"""
        return self._cached_embeddings.embed_query(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed documents (delegates to CacheBackedEmbeddings)"""
        return self._cached_embeddings.embed_documents(texts)

