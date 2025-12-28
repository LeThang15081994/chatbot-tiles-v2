"""
Redis Semantic Cache Implementation (Cache #4)
HNSW semantic search for similar queries
"""
import json
import uuid
import redis
from typing import Optional, List, Tuple
import asyncio
from app.src.application.interfaces.cache.semantic_cache_interface import ISemanticCache
from app.src.infrastructure.config.settings import RedisSettings


class RedisSemanticCache(ISemanticCache):
    """
    Redis implementation of ISemanticCache (Cache #4)

    Uses Redis Vector Search (RediSearch) with HNSW index
    Index name: idx:answer:semantic
    Uses Redis DB 0
    """

    def __init__(
        self,
        redis_settings: RedisSettings,
        dimension: int = 768,
        similarity_threshold: float = 0.8
    ):
        """
        Initialize Redis semantic cache

        Args:
            redis_settings: Redis configuration
            dimension: Embedding dimension
            similarity_threshold: Default similarity threshold
        """
        self.redis_client = None
        self.redis_settings = redis_settings
        self.dimension = dimension
        self.similarity_threshold = similarity_threshold
        self.index_name = "idx:answer:semantic"
        self.key_prefix = "answer:semantic:"
        self._connect()
        self._ensure_index()

    def _connect(self) -> None:
        """Connect to Redis"""
        self.redis_client = redis.Redis(
            host=self.redis_settings.REDIS_HOST,
            port=self.redis_settings.REDIS_PORT,
            db=0,  # Use DB 0 only
            password=self.redis_settings.REDIS_PASSWORD if self.redis_settings.REDIS_PASSWORD else None,
            decode_responses=False  # Need binary for vectors
        )

    def _ensure_index(self) -> None:
        """Ensure HNSW index exists"""
        try:
            # Check if index exists
            info = self.redis_client.execute_command("FT.INFO", self.index_name)
            if info:
                return  # Index exists
        except (redis.ResponseError, Exception):
            pass  # Index doesn't exist, create it

        try:
            # Create HNSW index (requires RediSearch module)
            # FT.CREATE idx:answer:semantic ON HASH PREFIX 1 answer:semantic: SCHEMA vector VECTOR HNSW 6 TYPE FLOAT32 DIM 768 DISTANCE_METRIC COSINE answer TEXT
            self.redis_client.execute_command(
                "FT.CREATE",
                self.index_name,
                "ON", "HASH",
                "PREFIX", "1", self.key_prefix,
                "SCHEMA",
                "vector", "VECTOR", "HNSW", "6", "TYPE", "FLOAT32", "DIM", str(self.dimension), "DISTANCE_METRIC", "COSINE",
                "answer", "TEXT"
            )
        except Exception as e:
            # RediSearch module not available or index already exists
            # Continue without semantic cache index (fallback to basic cache)
            pass

    async def search(
        self,
        query_vector: List[float],
        similarity_threshold: float = 0.8,
        top_k: int = 1
    ) -> Optional[Tuple[str, float]]:
        """
        Search for semantically similar cached answer

        Args:
            query_vector: Query embedding vector
            similarity_threshold: Minimum similarity score
            top_k: Number of results to return

        Returns:
            Tuple of (answer, similarity_score) if found, None otherwise
        """
        try:
            # Convert vector to bytes
            import struct
            vector_bytes = struct.pack(f'{len(query_vector)}f', *query_vector)

            # KNN search
            # FT.SEARCH idx:answer:semantic "*=>[KNN $k @vector $query_vector]" PARAMS 2 k 1 query_vector <vector_bytes> DIALECT 2
            results = await asyncio.to_thread(
                self.redis_client.execute_command,
                "FT.SEARCH",
                self.index_name,
                f"*=>[KNN $k @vector $query_vector]",
                "PARAMS", "2", "k", str(top_k), "query_vector", vector_bytes,
                "DIALECT", "2",
                "RETURN", "2", "answer", "vector"
            )

            if not results or len(results) < 2:
                return None

            # Parse results: [count, [key1, [field1, value1, field2, value2], ...]]
            count = results[0]
            if count == 0:
                return None

            # Get first result
            result_data = results[1]
            if len(result_data) < 3:
                return None

            key = result_data[0].decode('utf-8') if isinstance(result_data[0], bytes) else result_data[0]
            fields = result_data[1]

            # Extract answer and distance
            answer = None
            distance = 1.0

            for i in range(0, len(fields), 2):
                field_name = fields[i].decode('utf-8') if isinstance(fields[i], bytes) else fields[i]
                field_value = fields[i + 1]

                if field_name == "answer":
                    answer = field_value.decode('utf-8') if isinstance(field_value, bytes) else field_value
                elif field_name == "__vector_score":
                    distance = float(field_value.decode('utf-8') if isinstance(field_value, bytes) else field_value)

            # Convert distance to similarity (1 - distance for cosine)
            similarity = 1.0 - distance

            if answer and similarity >= similarity_threshold:
                return (answer, similarity)

            return None

        except Exception as e:
            print(f"Redis semantic cache search error: {e}")
            return None

    async def add(
        self,
        query_vector: List[float],
        answer: str,
        answer_id: Optional[str] = None
    ) -> bool:
        """
        Add answer to semantic cache

        Args:
            query_vector: Query embedding vector
            answer: Answer to cache
            answer_id: Optional answer ID

        Returns:
            True if successful
        """
        try:
            # Generate answer ID if not provided
            if not answer_id:
                answer_id = str(uuid.uuid4())

            key = f"{self.key_prefix}{answer_id}"

            # Convert vector to bytes
            import struct
            vector_bytes = struct.pack(f'{len(query_vector)}f', *query_vector)

            # Store in Redis hash
            await asyncio.to_thread(
                self.redis_client.hset,
                key,
                mapping={
                    "vector": vector_bytes,
                    "answer": answer
                }
            )

            return True

        except Exception as e:
            print(f"Redis semantic cache add error: {e}")
            return False

