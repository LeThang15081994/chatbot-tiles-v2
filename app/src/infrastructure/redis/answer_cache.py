"""
Answer Cache - Caches LLM Responses

This is separate from context cache:
- Context cache: caches retriever results (documents)
- Answer cache: caches LLM responses (answers)

Uses RedisSemanticCache for semantic similarity matching.
This allows finding cached answers for semantically similar questions.

Architecture:
LLM Response
  → Answer Cache (RedisSemanticCache)
    → Stores: query embedding → answer text
    → Lookup: query embedding → similar cached answer
"""
import json
import logging
from typing import Optional, Any
from langchain_redis import RedisSemanticCache
from langchain_core.outputs import Generation

from app.src.infrastructure.config.redis_settings import RedisSettings
from app.src.infrastructure.embeddings.onnx_embeddings import ONNXEmbeddings

logger = logging.getLogger(__name__)


class AnswerCache:
    """
    Answer Cache using RedisSemanticCache

    Caches LLM responses with semantic similarity matching.
    This is the ONLY place that uses RedisSemanticCache.

    Architecture:
    - Pre-cache: Before LLM call (TTL = 20 seconds)
    - Post-cache: After LLM + tools (TTL = 15 minutes)
    """

    def __init__(
        self,
        redis_settings: RedisSettings,
        embeddings: ONNXEmbeddings,
        distance_threshold: float = 0.2,
        pre_cache_ttl: int = 20,  # 20 seconds
        post_cache_ttl: int = 900  # 15 minutes
    ):
        """
        Initialize answer cache

        Args:
            redis_settings: Redis configuration
            embeddings: Embeddings instance (ONNXEmbeddings)
            distance_threshold: Similarity threshold
            pre_cache_ttl: Pre-cache TTL in seconds
            post_cache_ttl: Post-cache TTL in seconds
        """
        self.distance_threshold = distance_threshold
        self.pre_cache_ttl = pre_cache_ttl
        self.post_cache_ttl = post_cache_ttl

        # Build Redis URL
        redis_url = f"redis://{redis_settings.REDIS_HOST}:{redis_settings.REDIS_PORT}"
        if redis_settings.REDIS_PASSWORD:
            redis_url = f"redis://:{redis_settings.REDIS_PASSWORD}@{redis_settings.REDIS_HOST}:{redis_settings.REDIS_PORT}"

        # Initialize RedisSemanticCache for pre-cache
        self._pre_cache = RedisSemanticCache(
            embeddings=embeddings,
            redis_url=redis_url,
            distance_threshold=distance_threshold,
            ttl=pre_cache_ttl,
            name="answer_cache",
            prefix="answer_cache",
        )

        # Initialize RedisSemanticCache for post-cache
        self._post_cache = RedisSemanticCache(
            embeddings=embeddings,
            redis_url=redis_url,
            distance_threshold=distance_threshold,
            ttl=post_cache_ttl,
            name="answer_cache",
            prefix="answer_cache",
        )

        logger.info(
            f"AnswerCache initialized (threshold={distance_threshold}, "
            f"pre-cache TTL={pre_cache_ttl}s, post-cache TTL={post_cache_ttl}s)"
        )

    async def get(
        self,
        query: str,
        namespace: str = "pre-cache"
    ) -> Optional[str]:
        """
        Get cached answer for semantically similar query

        Args:
            query: Query text
            namespace: "pre-cache" or "post-cache"

        Returns:
            Cached answer if found, None otherwise
        """
        import asyncio
        try:
            cache = self._pre_cache if namespace == "pre-cache" else self._post_cache

            # Lookup in semantic cache (sync, run in thread pool)
            hits = await asyncio.to_thread(cache.lookup, query, namespace=namespace)

            if hits and isinstance(hits, list) and len(hits) > 0:
                hit = hits[0]
                if hasattr(hit, 'text'):
                    cached_data = json.loads(hit.text)

                    # Extract answer
                    if isinstance(cached_data, dict):
                        answer = cached_data.get("answer", "") or cached_data.get("response", "")
                    elif isinstance(cached_data, str):
                        answer = cached_data
                    else:
                        answer = None

                    if answer and answer.strip():
                        logger.info(f"Answer cache HIT [{namespace}] for query: {query[:50]}...")
                        return answer.strip()

            logger.info(f"Answer cache MISS [{namespace}] for query: {query[:50]}...")
            return None

        except Exception as e:
            logger.warning(f"Answer cache lookup error [{namespace}]: {e}")
            return None

    async def set(
        self,
        query: str,
        answer: str,
        namespace: str = "pre-cache"
    ) -> bool:
        """
        Cache answer for query

        Args:
            query: Query text
            answer: Answer to cache
            namespace: "pre-cache" or "post-cache"

        Returns:
            True if successful
        """
        import asyncio
        try:
            cache = self._pre_cache if namespace == "pre-cache" else self._post_cache

            # Prepare cache data
            cache_data = {
                "answer": str(answer).strip()
            }

            # Update cache (sync, run in thread pool)
            await asyncio.to_thread(
                cache.update,
                query,
                namespace=namespace,
                generations=[Generation(text=json.dumps(cache_data))],
            )

            logger.info(f"Answer cache STORED [{namespace}] for query: {query[:50]}...")
            return True

        except Exception as e:
            logger.error(f"Failed to store in answer cache [{namespace}]: {e}")
            return False

