"""
Health Check Use Case
"""
import time
from typing import List
from ..interfaces.health_repository import IHealthRepository
from ..dto.health_dto import (
    HealthCheckResponseDTO,
    ReadinessCheckResponseDTO,
    ServiceHealthDTO,
    HealthStatus
)


class HealthCheckUseCase:
    """
    Use case for system health checks

    Responsibilities:
    - Check health of all system components
    - Aggregate health status
    - Provide readiness and liveness checks
    """

    def __init__(
        self,
        health_repository: IHealthRepository,
        service_name: str = "Ceramic Tiles Chatbot",
        version: str = "1.0.0"
    ):
        """
        Initialize health check use case

        Args:
            health_repository: Health repository
            service_name: Service name
            version: Service version
        """
        self.health_repository = health_repository
        self.service_name = service_name
        self.version = version
        self.start_time = time.time()

    async def check_health(self) -> HealthCheckResponseDTO:
        """
        Check overall system health

        Returns:
            Health check response DTO
        """
        # Get system metrics
        metrics = await self.health_repository.get_system_metrics()

        # Check all services
        services: List[ServiceHealthDTO] = []

        # Database
        try:
            db_health = await self.health_repository.check_database_health()
            services.append(db_health)
        except Exception as e:
            services.append(ServiceHealthDTO(
                status=HealthStatus.UNHEALTHY,
                type="database",
                error=str(e)
            ))

        # Redis
        try:
            redis_health = await self.health_repository.check_redis_health()
            services.append(redis_health)
        except Exception as e:
            services.append(ServiceHealthDTO(
                status=HealthStatus.UNHEALTHY,
                type="redis",
                error=str(e)
            ))

        # Milvus
        try:
            milvus_health = await self.health_repository.check_milvus_health()
            services.append(milvus_health)
        except Exception as e:
            services.append(ServiceHealthDTO(
                status=HealthStatus.UNHEALTHY,
                type="milvus",
                error=str(e)
            ))

        # LLM
        try:
            llm_health = await self.health_repository.check_llm_health()
            services.append(llm_health)
        except Exception as e:
            services.append(ServiceHealthDTO(
                status=HealthStatus.UNHEALTHY,
                type="llm",
                error=str(e)
            ))

        # Embedding
        try:
            embedding_health = await self.health_repository.check_embedding_health()
            services.append(embedding_health)
        except Exception as e:
            services.append(ServiceHealthDTO(
                status=HealthStatus.UNHEALTHY,
                type="embedding",
                error=str(e)
            ))

        # Determine overall status
        overall_status = self._determine_overall_status(services)

        return HealthCheckResponseDTO(
            status=overall_status,
            service_name=self.service_name,
            version=self.version,
            uptime_seconds=metrics.get("uptime_seconds", 0),
            uptime_human=metrics.get("uptime_human", ""),
            timestamp=metrics.get("timestamp", ""),
            environment=metrics.get("environment", "unknown"),
            services=services
        )

    async def check_readiness(self) -> ReadinessCheckResponseDTO:
        """
        Check if service is ready to handle requests

        Returns:
            Readiness check response DTO
        """
        required_services = ["redis", "milvus", "llm"]
        ready_services = []
        not_ready_services = []

        # Check Redis
        try:
            redis_health = await self.health_repository.check_redis_health()
            if redis_health.status == HealthStatus.HEALTHY:
                ready_services.append("redis")
            else:
                not_ready_services.append("redis")
        except Exception:
            not_ready_services.append("redis")

        # Check Milvus
        try:
            milvus_health = await self.health_repository.check_milvus_health()
            if milvus_health.status == HealthStatus.HEALTHY:
                ready_services.append("milvus")
            else:
                not_ready_services.append("milvus")
        except Exception:
            not_ready_services.append("milvus")

        # Check LLM
        try:
            llm_health = await self.health_repository.check_llm_health()
            if llm_health.status == HealthStatus.HEALTHY:
                ready_services.append("llm")
            else:
                not_ready_services.append("llm")
        except Exception:
            not_ready_services.append("llm")

        is_ready = len(not_ready_services) == 0
        message = "Service is ready" if is_ready else f"Service not ready: {', '.join(not_ready_services)}"

        return ReadinessCheckResponseDTO(
            ready=is_ready,
            message=message,
            required_services=required_services,
            ready_services=ready_services,
            not_ready_services=not_ready_services
        )

    async def check_liveness(self) -> bool:
        """
        Check if service is alive (basic health check)

        Returns:
            True if service is alive
        """
        # Basic liveness check - service is running if we can execute this
        return True

    def _determine_overall_status(
        self,
        services: List[ServiceHealthDTO]
    ) -> HealthStatus:
        """
        Determine overall health status from individual services

        Args:
            services: List of service health statuses

        Returns:
            Overall health status
        """
        if not services:
            return HealthStatus.UNHEALTHY

        unhealthy_count = sum(
            1 for s in services
            if s.status == HealthStatus.UNHEALTHY
        )

        if unhealthy_count == 0:
            return HealthStatus.HEALTHY
        elif unhealthy_count < len(services):
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.UNHEALTHY

