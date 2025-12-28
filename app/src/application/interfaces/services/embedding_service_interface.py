"""
Embedding Service Interface (Cache #2)
ONLY place where /embed is called
"""
from abc import ABC, abstractmethod
from typing import List


class IEmbeddingService(ABC):
    """
    Interface for embedding service (Cache #2)

    This is the ONLY place where /embed is called.
    Handles embedding cache internally.
    """

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        This method:
        1. Checks cache first (key: embedding:{hash(text)})
        2. If miss, calls /embed API
        3. Saves to cache
        4. Returns embedding vector

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        pass

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        pass

