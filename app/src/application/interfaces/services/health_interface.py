"""
Health Service Interface
Abstract interface for health check service
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
from app.src.application.dto.health_dto import ServiceHealthDTO


class IHealthService(ABC):
    """
    Interface for health check service

    Application layer interface - no infrastructure dependencies.
    Allows Application layer to check system health without depending on concrete implementations.
    """

    @abstractmethod
    async def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get system metrics (uptime, memory, etc.)

        Returns:
            Dictionary with system metrics:
            - uptime_seconds: float
            - uptime_human: str
            - timestamp: str
            - environment: str
        """
        pass

    @abstractmethod
    async def check_database_health(self) -> ServiceHealthDTO:
        """
        Check database health

        Returns:
            ServiceHealthDTO with database health status
        """
        pass

    @abstractmethod
    async def check_redis_health(self) -> ServiceHealthDTO:
        """
        Check Redis cache health

        Returns:
            ServiceHealthDTO with Redis health status
        """
        pass

    @abstractmethod
    async def check_milvus_health(self) -> ServiceHealthDTO:
        """
        Check Milvus vector database health

        Returns:
            ServiceHealthDTO with Milvus health status
        """
        pass

    @abstractmethod
    async def check_llm_health(self) -> ServiceHealthDTO:
        """
        Check LLM service health

        Returns:
            ServiceHealthDTO with LLM health status
        """
        pass

    @abstractmethod
    async def check_embedding_health(self) -> ServiceHealthDTO:
        """
        Check embedding service health

        Returns:
            ServiceHealthDTO with embedding service health status
        """
        pass

