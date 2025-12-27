"""
Redis Infrastructure Module

All Redis-related cache implementations are located here:
- AnswerCache: LLM response cache with semantic similarity
- ContextCache: Retriever result cache
- CachedONNXEmbeddings: Embedding cache wrapper (uses Redis)
- CachedRetriever: Retriever with context cache (uses Redis)

Removed:
- RedisCacheRepository: Not used in pipeline (removed)
- SemanticCacheRepository: Deprecated, replaced by AnswerCache + ContextCache (removed)
"""
from .answer_cache import AnswerCache
from .context_cache import ContextCache
from .cached_embeddings import CachedONNXEmbeddings
from .cached_retriever import CachedRetriever

__all__ = [
    "AnswerCache",  # LLM response cache
    "ContextCache",  # Retriever result cache
    "CachedONNXEmbeddings",  # Embedding cache wrapper
    "CachedRetriever",  # Retriever with context cache
]

