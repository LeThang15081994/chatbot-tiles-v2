"""
ONNX Embeddings - Single Source of Truth for Embeddings

This is the ONLY Embeddings implementation following LangChain OSS best practices:
- Inherits from langchain_core.embeddings.Embeddings
- SYNC ONLY (no async/await)
- ONLY calls HTTP endpoint /embed
- NO cache logic
- NO orchestration logic
- ONLY implements embed_query() and embed_documents()

Embedding caching is handled by CacheBackedEmbeddings (separate layer).
"""
from typing import List
import requests
from langchain_core.embeddings import Embeddings

from app.src.infrastructure.config.embedding_settings import EmbeddingSettings


class ONNXEmbeddings(Embeddings):
    """
    ONNX Service Embeddings Implementation

    This is the ONLY Embeddings class in the system.
    It follows LangChain OSS architecture:
    - Sync only (required by LangChain Embeddings interface)
    - Direct HTTP call to embedding service
    - No caching (handled by CacheBackedEmbeddings)
    - No orchestration (handled by Retriever)

    Architecture:
    - Retriever.invoke(query)
      → CacheBackedEmbeddings (checks Redis cache)
        → ONNXEmbeddings.embed_query() (only on cache MISS)
          → requests.post("/embed")
    """

    def __init__(self, settings: EmbeddingSettings):
        """
        Initialize ONNX embeddings

        Args:
            settings: Embedding configuration settings
        """
        super().__init__()
        self.settings = settings
        self.service_url = settings.ONNX_SERVICE_URL
        self.dimension = settings.EMBEDDING_DIMENSION
        self.model_name = settings.EMBEDDING_MODEL

    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        This method is called by:
        - Retriever (via CacheBackedEmbeddings)
        - RedisSemanticCache (for answer caching, separate concern)

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        try:
            response = requests.post(
                f"{self.service_url}/embed",
                json={"texts": [text]},
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

            # Handle different response formats
            if "embeddings" in result:
                embeddings = result["embeddings"]
                if not embeddings:
                    raise RuntimeError("No embeddings returned")
                return embeddings[0]
            elif "embedding" in result:
                return result["embedding"]
            else:
                raise RuntimeError(f"Unexpected response format: {result.keys()}")

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to call embedding service: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to generate embedding: {e}")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts

        This method is called by:
        - Retriever (for batch processing)
        - Document ingestion (if needed)

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            response = requests.post(
                f"{self.service_url}/embed",
                json={"texts": texts},
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()

            # Handle different response formats
            if "embeddings" in result:
                return result["embeddings"]
            elif "embedding" in result:
                # Single embedding returned, wrap in list
                return [result["embedding"]]
            else:
                raise RuntimeError(f"Unexpected response format: {result.keys()}")

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to call embedding service: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to generate embeddings: {e}")

