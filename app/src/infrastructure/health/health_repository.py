"""
Health Repository Implementation
Provides health check functionality for all services
"""
import time
from typing import Dict, Any
from datetime import datetime

from app.src.application.interfaces.health_repository import IHealthRepository
from app.src.application.dto.health_dto import ServiceHealthDTO, HealthStatus


class HealthRepository(IHealthRepository):
    """
    Health repository implementation

    Aggregates health checks from various services
    """

    def __init__(
        self,
        vector_store,
        context_cache=None,  # Use context_cache to check Redis health
        llm_client=None,
        database=None,
        embedding_service=None
    ):
        """
        Initialize health repository

        Args:
            vector_store: Milvus vector store repository
            context_cache: Context cache (has Redis client for health check)
            llm_client: LLM client
            database: PostgreSQL database
            embedding_service: Embedding service (optional)
        """
        self.vector_store = vector_store
        self.context_cache = context_cache
        self.llm_client = llm_client
        self.database = database
        self.embedding_service = embedding_service
        self.start_time = time.time()

    async def check_database_health(self) -> ServiceHealthDTO:
        """Check PostgreSQL database health"""
        start = time.time()
        try:
            # Simple health check - try to execute a query
            await self.database.fetchval("SELECT 1")
            response_time = int((time.time() - start) * 1000)

            return ServiceHealthDTO(
                status=HealthStatus.HEALTHY,
                type="database",
                response_time_ms=response_time,
                details={"type": "postgresql"}
            )
        except Exception as e:
            return ServiceHealthDTO(
                status=HealthStatus.UNHEALTHY,
                type="database",
                error=str(e),
                details={"type": "postgresql"}
            )

    async def check_redis_health(self) -> ServiceHealthDTO:
        """Check Redis cache health"""
        start = time.time()
        try:
            # Check Redis connection via context_cache
            if self.context_cache and hasattr(self.context_cache, 'redis_client'):
                # Try to ping Redis
                self.context_cache.redis_client.ping()
                healthy = True
            else:
                healthy = False

            response_time = int((time.time() - start) * 1000)

            return ServiceHealthDTO(
                status=HealthStatus.HEALTHY if healthy else HealthStatus.UNHEALTHY,
                type="redis",
                response_time_ms=response_time
            )
        except Exception as e:
            return ServiceHealthDTO(
                status=HealthStatus.UNHEALTHY,
                type="redis",
                error=str(e)
            )

    async def check_milvus_health(self) -> ServiceHealthDTO:
        """Check Milvus vector database health"""
        start = time.time()
        try:
            healthy = await self.vector_store.health_check()
            response_time = int((time.time() - start) * 1000)

            return ServiceHealthDTO(
                status=HealthStatus.HEALTHY if healthy else HealthStatus.UNHEALTHY,
                type="milvus",
                response_time_ms=response_time
            )
        except Exception as e:
            return ServiceHealthDTO(
                status=HealthStatus.UNHEALTHY,
                type="milvus",
                error=str(e)
            )

    async def check_llm_health(self) -> ServiceHealthDTO:
        """Check LLM service health"""
        start = time.time()
        try:
            healthy = await self.llm_client.health_check()
            response_time = int((time.time() - start) * 1000)

            return ServiceHealthDTO(
                status=HealthStatus.HEALTHY if healthy else HealthStatus.UNHEALTHY,
                type="llm",
                response_time_ms=response_time
            )
        except Exception as e:
            return ServiceHealthDTO(
                status=HealthStatus.UNHEALTHY,
                type="llm",
                error=str(e)
            )

    async def check_embedding_health(self) -> ServiceHealthDTO:
        """Check embedding service health"""
        start = time.time()
        try:
            if self.embedding_service:
                healthy = await self.embedding_service.health_check()
            else:
                healthy = False
            response_time = int((time.time() - start) * 1000)

            return ServiceHealthDTO(
                status=HealthStatus.HEALTHY if healthy else HealthStatus.UNHEALTHY,
                type="embedding",
                response_time_ms=response_time
            )
        except Exception as e:
            return ServiceHealthDTO(
                status=HealthStatus.UNHEALTHY,
                type="embedding",
                error=str(e)
            )

    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get system metrics (uptime, memory, etc.)"""
        uptime_seconds = time.time() - self.start_time

        # Convert to human-readable format
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        seconds = int(uptime_seconds % 60)
        uptime_human = f"{hours}h {minutes}m {seconds}s"

        return {
            "uptime_seconds": uptime_seconds,
            "uptime_human": uptime_human,
            "timestamp": datetime.now().isoformat(),
            "environment": "development"  # TODO: Get from settings
        }

