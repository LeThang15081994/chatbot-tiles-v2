"""
Embedding Repository Interface
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class IEmbeddingRepository(ABC):
    """
    Interface for embedding operations
    Abstracts the underlying embedding model (Sentence Transformers, OpenAI, etc.)
    """

    @abstractmethod
    async def embed_text(
        self,
        text: str
    ) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Input text

        Returns:
            Embedding vector
        """
        pass

    @abstractmethod
    async def embed_texts(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts

        Args:
            texts: List of input texts
            batch_size: Batch size for processing

        Returns:
            List of embedding vectors
        """
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """
        Get embedding dimension

        Returns:
            Embedding vector dimension
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """
        Get embedding model name

        Returns:
            Model name
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if embedding service is healthy

        Returns:
            True if healthy
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get embedding model information

        Returns:
            Dictionary with model info (name, dimension, max_length, etc.)
        """
        pass

    @abstractmethod
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get embedding cache information

        Returns:
            Dictionary with cache stats if available
        """
        pass

