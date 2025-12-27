"""
ONNX Service Embedding Implementation
Uses lightweight ONNX service (no Triton needed)
"""
from typing import List, Dict, Any
import httpx
import numpy as np

from app.src.application.interfaces.embedding_repository import IEmbeddingRepository
from app.src.infrastructure.config.embedding_settings import EmbeddingSettings


class ONNXServiceEmbedding(IEmbeddingRepository):
    """
    ONNX Service embedding implementation

    Uses lightweight FastAPI service running ONNX Runtime
    Much smaller than Triton (500MB vs 22GB)
    """

    def __init__(self, settings: EmbeddingSettings):
        """
        Initialize ONNX service embedding

        Args:
            settings: Embedding configuration settings
        """
        self.settings = settings
        self.service_url = settings.ONNX_SERVICE_URL
        self.dimension = settings.EMBEDDING_DIMENSION # paraphrase-multilingual-mpnet-base-v2
        self.model_name = settings.EMBEDDING_MODEL  # Default: paraphrase-multilingual-mpnet-base-v2

        # HTTP client with connection pooling
        self.client = httpx.AsyncClient(
            base_url=self.service_url,
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )

    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text (IEmbeddingRepository interface)

        Args:
            text: Text to embed

        Returns:
            Embedding vector (dimension)
        """
        try:
            response = await self.client.post(
                "/embed",
                json={"texts": [text]}
            )
            response.raise_for_status()

            result = response.json()
            embeddings = result["embeddings"]

            if not embeddings:
                raise RuntimeError("No embeddings returned")

            return embeddings[0]

        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"ONNX service error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise RuntimeError(f"Failed to generate embedding via ONNX service: {e}")

    async def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for single text (alias for embed_text)

        Args:
            text: Text to embed

        Returns:
            Embedding vector (dimension)
        """
        return await self.embed_text(text)

    async def embed_texts(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (IEmbeddingRepository interface)

        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing (used for chunking large batches)

        Returns:
            List of embedding vectors
        """
        try:
            # Process in batches if needed
            if len(texts) <= batch_size:
                response = await self.client.post(
                    "/embed",
                    json={"texts": texts}
                )
                response.raise_for_status()

                result = response.json()
                embeddings = result["embeddings"]

                return embeddings
            else:
                # Process in batches
                all_embeddings = []
                for i in range(0, len(texts), batch_size):
                    batch = texts[i:i + batch_size]
                    response = await self.client.post(
                        "/embed",
                        json={"texts": batch}
                    )
                    response.raise_for_status()

                    result = response.json()
                    embeddings = result["embeddings"]
                    all_embeddings.extend(embeddings)

                return all_embeddings

        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"ONNX service error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise RuntimeError(f"Failed to generate embeddings via ONNX service: {e}")

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (alias for embed_texts)

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        return await self.embed_texts(texts)

    def get_dimension(self) -> int:
        """
        Get embedding dimension

        Returns:
            Embedding vector dimension
        """
        return self.dimension

    def get_model_name(self) -> str:
        """
        Get embedding model name

        Returns:
            Model name
        """
        return self.model_name

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get embedding model information

        Returns:
            Dictionary with model info (name, dimension, service_url, etc.)
        """
        return {
            "name": self.model_name,
            "dimension": self.dimension,
            "service_url": self.service_url,
            "provider": "onnx-service"
        }

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get embedding cache information

        Returns:
            Dictionary with cache stats if available (empty for ONNX service)
        """
        return {}  # ONNX service doesn't have built-in cache

    def embed_query_sync(self, text: str) -> List[float]:
        """
        Synchronous embedding generation (for LangChain compatibility)

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.embed_text(text))
        except RuntimeError:
            return asyncio.run(self.embed_text(text))

    async def health_check(self) -> bool:
        """
        Check ONNX service health

        Returns:
            True if service is healthy
        """
        try:
            response = await self.client.get("/health")
            if response.status_code != 200:
                return False

            result = response.json()
            return result.get("status") == "healthy" and result.get("model_loaded", False)

        except Exception:
            return False

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    def __del__(self):
        """Cleanup on deletion"""
        try:
            import asyncio
            # Try to close the client synchronously if possible
            # If in async context, the client will be closed when event loop shuts down
            if hasattr(self, 'client') and self.client:
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # Can't await in __del__, just schedule for cleanup
                        loop.create_task(self.close())
                    else:
                        loop.run_until_complete(self.close())
                except (RuntimeError, AttributeError):
                    # No event loop or already closed, skip cleanup
                    pass
        except Exception:
            pass

