"""
Health Check Repository Interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from app.src.application.dto.health_dto import ServiceHealthDTO, HealthStatus


class IHealthRepository(ABC):
    """
    Interface for health check operations
    """

    @abstractmethod
    async def check_database_health(self) -> ServiceHealthDTO:
        """
        Check PostgreSQL database health

        Returns:
            Service health status
        """
        pass

    @abstractmethod
    async def check_redis_health(self) -> ServiceHealthDTO:
        """
        Check Redis cache health

        Returns:
            Service health status
        """
        pass

    @abstractmethod
    async def check_milvus_health(self) -> ServiceHealthDTO:
        """
        Check Milvus vector database health

        Returns:
            Service health status
        """
        pass

    @abstractmethod
    async def check_llm_health(self) -> ServiceHealthDTO:
        """
        Check LLM service health

        Returns:
            Service health status
        """
        pass

    @abstractmethod
    async def check_embedding_health(self) -> ServiceHealthDTO:
        """
        Check embedding service health

        Returns:
            Service health status
        """
        pass

    @abstractmethod
    async def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get system metrics (uptime, memory, etc.)

        Returns:
            Dictionary with system metrics
        """
        pass

