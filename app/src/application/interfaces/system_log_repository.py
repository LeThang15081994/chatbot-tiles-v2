"""
System Log Repository Interface
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from ..dto.system_log_dto import (
    SystemLogCreateDTO,
    SystemLogDTO,
    SystemLogQueryDTO,
    SystemLogResponseDTO,
    LogStatsDTO,
)


class ISystemLogRepository(ABC):
    """
    Interface for system logging operations
    """

    @abstractmethod
    async def create_log(
        self,
        log: SystemLogCreateDTO
    ) -> int:
        """
        Create a system log entry

        Args:
            log: Log data to create

        Returns:
            Created log ID
        """
        pass

    @abstractmethod
    async def get_logs(
        self,
        query: SystemLogQueryDTO
    ) -> SystemLogResponseDTO:
        """
        Query system logs with filters and pagination

        Args:
            query: Query filters

        Returns:
            List of logs matching query
        """
        pass

    @abstractmethod
    async def get_log_by_id(
        self,
        log_id: int
    ) -> Optional[SystemLogDTO]:
        """
        Get a specific log entry by ID

        Args:
            log_id: Log ID

        Returns:
            Log entry if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_stats(
        self,
        service_name: Optional[str] = None
    ) -> List[LogStatsDTO]:
        """
        Get log statistics by service

        Args:
            service_name: Optional service name filter

        Returns:
            List of statistics per service
        """
        pass

    @abstractmethod
    async def delete_old_logs(
        self,
        days: int = 30
    ) -> int:
        """
        Delete logs older than specified days (for maintenance)

        Args:
            days: Number of days to keep

        Returns:
            Number of logs deleted
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if logging system is healthy

        Returns:
            True if healthy
        """
        pass

