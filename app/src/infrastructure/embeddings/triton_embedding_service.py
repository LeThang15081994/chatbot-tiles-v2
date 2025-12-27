"""
Triton Embedding Service Implementation
Generates embeddings using Triton Inference Server
"""
from typing import List
import httpx
import numpy as np

from app.src.application.interfaces.embedding_repository import IEmbeddingRepository
from app.src.infrastructure.config.embedding_settings import EmbeddingSettings


class TritonEmbeddingService(IEmbeddingRepository):
    """
    Triton Inference Server implementation for embeddings

    Uses paraphrase-multilingual-mpnet-base-v2 model deployed on Triton
    Dimension: 768
    Supports 50+ languages including Vietnamese
    """

    def __init__(self, settings: EmbeddingSettings):
        """
        Initialize Triton embedding service

        Args:
            settings: Embedding configuration settings
        """
        self.settings = settings
        self.triton_url = settings.TRITON_URL
        self.model_name = "embeddings"
        self.dimension = 768  # paraphrase-multilingual-mpnet-base-v2 dimension

        # HTTP client with connection pooling
        self.client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )

    async def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for single text

        Args:
            text: Text to embed

        Returns:
            Embedding vector (768 dimensions)
        """
        try:
            # Prepare request
            payload = {
                "inputs": [{
                    "name": "text",
                    "datatype": "BYTES",
                    "shape": [1],
                    "data": [text]
                }]
            }

            # Send request to Triton
            response = await self.client.post(
                f"{self.triton_url}/v2/models/{self.model_name}/infer",
                json=payload
            )
            response.raise_for_status()

            # Parse response
            result = response.json()
            embedding = result["outputs"][0]["data"]

            return embedding

        except Exception as e:
            raise RuntimeError(f"Failed to generate embedding via Triton: {e}")

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            # Prepare request for batch
            payload = {
                "inputs": [{
                    "name": "text",
                    "datatype": "BYTES",
                    "shape": [len(texts)],
                    "data": texts
                }]
            }

            # Send request to Triton
            response = await self.client.post(
                f"{self.triton_url}/v2/models/{self.model_name}/infer",
                json=payload
            )
            response.raise_for_status()

            # Parse response
            result = response.json()
            embeddings_flat = result["outputs"][0]["data"]

            # Reshape to [batch_size, 768]
            embeddings = np.array(embeddings_flat).reshape(len(texts), self.dimension)

            return embeddings.tolist()

        except Exception as e:
            raise RuntimeError(f"Failed to generate embeddings via Triton: {e}")

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
            # Run async function in sync context
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.embed_query(text))
        except RuntimeError:
            # If no event loop, create new one
            return asyncio.run(self.embed_query(text))

    async def health_check(self) -> bool:
        """
        Check Triton server health

        Returns:
            True if server is healthy
        """
        try:
            # Check server health
            response = await self.client.get(f"{self.triton_url}/v2/health/ready")
            if response.status_code != 200:
                return False

            # Check model readiness
            response = await self.client.get(
                f"{self.triton_url}/v2/models/{self.model_name}/ready"
            )
            return response.status_code == 200

        except Exception:
            return False

    async def get_model_info(self) -> dict:
        """
        Get model information from Triton

        Returns:
            Dictionary with model info
        """
        try:
            response = await self.client.get(
                f"{self.triton_url}/v2/models/{self.model_name}/config"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

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

