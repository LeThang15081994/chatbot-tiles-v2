"""
Health Controller
Handles health check and system status requests
"""
from datetime import datetime
from typing import Dict, Any

from app.src.application.use_cases.health_check_use_case import HealthCheckUseCase
from app.src.application.dto.health_dto import HealthCheckResponseDTO


class HealthController:
    """
    Health Controller

    Provides system health and status information
    """

    def __init__(
        self,
        health_check_use_case: HealthCheckUseCase,
    ):
        """
        Initialize health controller

        Args:
            health_check_use_case: Health check use case
        """
        self.health_check_use_case = health_check_use_case

    async def health_check(self) -> HealthCheckResponseDTO:
        """
        Perform health check on all services

        Returns:
            Health check response DTO
        """
        # Use HealthCheckUseCase
        health_dto = await self.health_check_use_case.check_health()
        return health_dto

    async def readiness_check(self) -> Dict[str, Any]:
        """
        Check if service is ready to accept requests

        Returns:
            Readiness status
        """
        # Use HealthCheckUseCase
        readiness_dto = await self.health_check_use_case.check_readiness()

        return {
            "ready": readiness_dto.ready,
            "message": readiness_dto.message,
            "required_services": readiness_dto.required_services,
            "ready_services": readiness_dto.ready_services,
            "not_ready_services": readiness_dto.not_ready_services,
            "timestamp": datetime.now().isoformat(),
        }

    async def liveness_check(self) -> Dict[str, Any]:
        """
        Check if service is alive

        Returns:
            Liveness status
        """
        # Use HealthCheckUseCase
        is_alive = await self.health_check_use_case.check_liveness()

        return {
            "alive": is_alive,
            "timestamp": datetime.now().isoformat(),
        }
