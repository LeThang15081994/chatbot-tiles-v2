"""
Embedding Service Wrapper
Implements IEmbeddingService interface
Wraps CachedONNXEmbeddings (which handles Cache #2)
"""
from typing import List
from langchain_core.embeddings import Embeddings
from app.src.application.interfaces.services.embedding_service_interface import IEmbeddingService


class EmbeddingServiceWrapper(IEmbeddingService):
    """
    Wrapper around CachedONNXEmbeddings that implements IEmbeddingService

    This is the ONLY place where /embed is called.
    The underlying CachedONNXEmbeddings handles:
    - Cache #2: Embedding cache (key: embedding:{hash(text)})
    - Actual /embed API call (only on cache miss)
    """

    def __init__(self, cached_embeddings: Embeddings):
        """
        Initialize embedding service wrapper

        Args:
            cached_embeddings: CachedONNXEmbeddings instance (or any Embeddings)
        """
        self.cached_embeddings = cached_embeddings

    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        This is the ONLY place where /embed is called.
        The CachedONNXEmbeddings instance handles:
        1. Check cache (key: embedding:{hash(text)})
        2. If miss, call /embed API
        3. Save to cache
        4. Return embedding vector

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        return self.cached_embeddings.embed_query(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        return self.cached_embeddings.embed_documents(texts)

