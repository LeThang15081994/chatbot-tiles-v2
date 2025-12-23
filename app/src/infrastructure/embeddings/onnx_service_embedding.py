"""
ONNX Service Embedding Implementation
Uses lightweight ONNX service (no Triton needed)
"""
from typing import List
import httpx
import numpy as np

from app.src.application.interfaces.embedding_repository import IEmbedding
from app.src.infrastructure.config.embedding_settings import EmbeddingSettings


class ONNXServiceEmbedding(IEmbedding):
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

        # HTTP client with connection pooling
        self.client = httpx.AsyncClient(
            base_url=self.service_url,
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )

    async def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for single text

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

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            response = await self.client.post(
                "/embed",
                json={"texts": texts}
            )
            response.raise_for_status()

            result = response.json()
            embeddings = result["embeddings"]

            return embeddings

        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"ONNX service error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise RuntimeError(f"Failed to generate embeddings via ONNX service: {e}")

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
            return loop.run_until_complete(self.embed_query(text))
        except RuntimeError:
            return asyncio.run(self.embed_query(text))

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
            asyncio.create_task(self.close())
        except Exception:
            pass

