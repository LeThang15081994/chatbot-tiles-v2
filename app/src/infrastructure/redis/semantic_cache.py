"""
Semantic Cache Implementation using LangChain RedisSemanticCache
Similar to code cũ implementation
"""
import json
import logging
from typing import Optional, Any, List
from langchain_redis import RedisSemanticCache
from langchain_core.outputs import Generation

from app.src.application.interfaces.cache_repository import ISemanticCacheRepository
from app.src.application.interfaces.embedding_repository import IEmbeddingRepository
from app.src.infrastructure.config.redis_settings import RedisSettings

logger = logging.getLogger(__name__)


class LangChainEmbeddingWrapper:
    """
    Wrapper to convert IEmbeddingRepository to LangChain-compatible format
    """
    def __init__(self, embedding_service: IEmbeddingRepository):
        self.embedding_service = embedding_service

    def embed_query(self, text: str) -> List[float]:
        """Synchronous embedding for LangChain"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Try embed_text first (IEmbeddingRepository), fallback to embed_query (IEmbedding)
        if hasattr(self.embedding_service, 'embed_text'):
            return loop.run_until_complete(self.embedding_service.embed_text(text))
        elif hasattr(self.embedding_service, 'embed_query'):
            return loop.run_until_complete(self.embedding_service.embed_query(text))
        else:
            raise AttributeError("Embedding service must have embed_text or embed_query method")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Synchronous embedding for LangChain"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Try embed_texts first (IEmbeddingRepository), fallback to embed_documents (IEmbedding)
        if hasattr(self.embedding_service, 'embed_texts'):
            return loop.run_until_complete(self.embedding_service.embed_texts(texts))
        elif hasattr(self.embedding_service, 'embed_documents'):
            return loop.run_until_complete(self.embedding_service.embed_documents(texts))
        else:
            raise AttributeError("Embedding service must have embed_texts or embed_documents method")


class SemanticCacheRepository(ISemanticCacheRepository):
    """
    Semantic Cache Repository using RedisSemanticCache from langchain_redis
    Similar to code cũ's SemanticCacheLLMs

    Supports two cache namespaces:
    - pre-cache: Cache before LLM call (TTL = 20 seconds)
    - post-cache: Cache after tool execution (TTL = 15 minutes)
    """

    def __init__(
        self,
        redis_settings: RedisSettings,
        embedding_service: IEmbeddingRepository,
        distance_threshold: float = 0.2,
        pre_cache_ttl: int = 20,  # 20 seconds for pre-cache (before LLM call)
        post_cache_ttl: int = 900  # 15 minutes for post-cache (after tool execution)
    ):
        """
        Initialize semantic cache with two namespaces

        Args:
            redis_settings: Redis configuration
            embedding_service: Embedding service for semantic similarity
            distance_threshold: Similarity threshold (0.0 to 1.0, lower = more strict)
            pre_cache_ttl: TTL for pre-cache (before LLM call) in seconds
            post_cache_ttl: TTL for post-cache (after tool execution) in seconds
        """
        self.redis_settings = redis_settings
        self.distance_threshold = distance_threshold
        self.pre_cache_ttl = pre_cache_ttl
        self.post_cache_ttl = post_cache_ttl

        # Build Redis URL
        redis_url = f"redis://{redis_settings.REDIS_HOST}:{redis_settings.REDIS_PORT}"
        if redis_settings.REDIS_PASSWORD:
            redis_url = f"redis://:{redis_settings.REDIS_PASSWORD}@{redis_settings.REDIS_HOST}:{redis_settings.REDIS_PORT}"

        # Wrap embedding service for LangChain
        embedding_wrapper = LangChainEmbeddingWrapper(embedding_service)

        # Initialize RedisSemanticCache for pre-cache (TTL = 20 seconds)
        self._pre_cache = RedisSemanticCache(
            embeddings=embedding_wrapper,
            redis_url=redis_url,
            distance_threshold=distance_threshold,
            ttl=pre_cache_ttl,
            name="llm_cache",
            prefix="llmcache",
        )

        # Initialize RedisSemanticCache for post-cache (TTL = 15 minutes)
        self._post_cache = RedisSemanticCache(
            embeddings=embedding_wrapper,
            redis_url=redis_url,
            distance_threshold=distance_threshold,
            ttl=post_cache_ttl,
            name="llm_cache",
            prefix="llmcache",
        )

        logger.info(
            f"SemanticCacheRepository initialized (threshold={distance_threshold}, "
            f"pre-cache TTL={pre_cache_ttl}s, post-cache TTL={post_cache_ttl}s)"
        )

    async def get_similar(
        self,
        query: str,
        threshold: float = 0.95,
        namespace: str = "pre-cache"
    ) -> Optional[Any]:
        """
        Get cached value for semantically similar query

        Args:
            query: Query text
            threshold: Similarity threshold (0.0 to 1.0)
                      Note: This is converted to distance_threshold (1.0 - threshold)
            namespace: Cache namespace ("pre-cache" or "post-cache")

        Returns:
            Cached value if similar query exists, None otherwise
        """
        try:
            # Select cache based on namespace
            cache = self._pre_cache if namespace == "pre-cache" else self._post_cache

            # Lookup in semantic cache
            hits = cache.lookup(query, namespace=namespace)

            if hits and isinstance(hits, list) and len(hits) > 0:
                hit = hits[0]
                if hasattr(hit, 'text'):
                    cached_data = json.loads(hit.text)

                    # Extract response from cached data
                    if isinstance(cached_data, dict):
                        response = cached_data.get("response", "") or cached_data.get("data", "") or cached_data.get("text", "")
                    elif isinstance(cached_data, str):
                        response = cached_data
                    else:
                        response = None

                    if response and response.strip():
                        logger.info(f"Semantic cache HIT [{namespace}] for query: {query[:50]}...")
                        return response.strip()

            logger.info(f"Semantic cache MISS [{namespace}] for query: {query[:50]}...")
            return None

        except Exception as e:
            logger.warning(f"Semantic cache lookup error [{namespace}]: {e}")
            return None

    async def set_with_embedding(
        self,
        query: str,
        value: Any,
        embedding: Optional[List[float]] = None,
        ttl: Optional[int] = None,
        namespace: str = "pre-cache"
    ) -> bool:
        """
        Set value in cache with query embedding for semantic matching

        Args:
            query: Query text
            value: Value to cache
            embedding: Pre-computed embedding (ignored, computed automatically)
            ttl: Time to live in seconds (ignored, uses namespace-specific TTL)
            namespace: Cache namespace ("pre-cache" or "post-cache")

        Returns:
            True if successful
        """
        try:
            # Select cache based on namespace
            cache = self._pre_cache if namespace == "pre-cache" else self._post_cache

            # Prepare cache data (same format as code cũ)
            cache_data = {
                "response": str(value).strip()
            }

            # Update cache (same as code cũ)
            cache.update(
                query,
                namespace=namespace,
                generations=[Generation(text=json.dumps(cache_data))],
            )

            logger.info(f"Semantic cache STORED [{namespace}] for query: {query[:50]}...")
            return True

        except Exception as e:
            logger.error(f"Failed to store in semantic cache [{namespace}]: {e}")
            return False

    # Implement ICacheRepository methods (delegated to semantic cache)
    async def get(self, key: str) -> Optional[Any]:
        """Get value by exact key (not semantic)"""
        # For exact key lookup, we'd need direct Redis access
        # This is a fallback - semantic cache doesn't support exact keys
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value by exact key (not semantic)"""
        # Semantic cache doesn't support exact keys
        return False

    async def delete(self, key: str) -> bool:
        """Delete key (not supported by semantic cache)"""
        return False

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        return False

    async def clear(self, pattern: Optional[str] = None) -> int:
        """Clear cache entries"""
        return 0

    async def get_ttl(self, key: str) -> Optional[int]:
        """Get TTL for key (returns post-cache TTL as default)"""
        return self.post_cache_ttl

    async def health_check(self) -> bool:
        """Check cache health"""
        try:
            # Try a simple lookup to test connection
            self._cache.lookup("health_check", namespace="rag_cache")
            return True
        except Exception:
            return False

    async def get_stats(self) -> dict:
        """Get cache statistics"""
        return {
            "type": "semantic_cache",
            "distance_threshold": self.distance_threshold,
            "pre_cache_ttl": self.pre_cache_ttl,
            "post_cache_ttl": self.post_cache_ttl,
            "prefix": "llmcache",
            "name": "llm_cache"
        }

