"""
System Log Use Case
Handles logging of critical system events to files

Application logs được ghi ra file và KHÔNG lưu vào PostgreSQL theo thiết kế.
Hệ thống logging sử dụng file rotation theo ngày và tự động xóa log cũ hơn 15 ngày.
"""
import traceback
from typing import Optional
from app.src.application.interfaces.system_log_repository import ISystemLogRepository
from app.src.application.dto.system_log_dto import (
    SystemLogLevel,
    SystemLogCreateDTO,
    SystemLogQueryDTO,
    SystemLogResponseDTO,
    LogStatsDTO,
)


class SystemLogUseCase:
    """
    Use case for system logging

    Responsibilities:
    - Log critical system events to files (NOT database)
    - Query logs for monitoring and debugging
    - Provide log statistics
    - Manage log retention (15 days by default)

    Application logs được ghi ra file và KHÔNG lưu vào PostgreSQL theo thiết kế.
    """

    def __init__(
        self,
        log_repository: ISystemLogRepository,
    ):
        """
        Initialize system log use case

        Args:
            log_repository: System log repository
        """
        self.log_repository = log_repository

    async def log_info(
        self,
        service_name: str,
        message: str,
        metadata: Optional[dict] = None
    ) -> int:
        """
        Log an INFO level message

        Args:
            service_name: Service name (e.g., "chatbot", "api")
            message: Log message
            metadata: Optional metadata

        Returns:
            Log ID
        """
        log = SystemLogCreateDTO(
            service_name=service_name,
            level=SystemLogLevel.INFO,
            message=message,
            metadata=metadata
        )
        return await self.log_repository.create_log(log)

    async def log_warning(
        self,
        service_name: str,
        message: str,
        metadata: Optional[dict] = None
    ) -> int:
        """
        Log a WARNING level message

        Args:
            service_name: Service name
            message: Log message
            metadata: Optional metadata

        Returns:
            Log ID
        """
        log = SystemLogCreateDTO(
            service_name=service_name,
            level=SystemLogLevel.WARN,
            message=message,
            metadata=metadata
        )
        return await self.log_repository.create_log(log)

    async def log_error(
        self,
        service_name: str,
        message: str,
        error: Optional[Exception] = None,
        metadata: Optional[dict] = None
    ) -> int:
        """
        Log an ERROR level message

        Args:
            service_name: Service name
            message: Log message
            error: Optional exception
            metadata: Optional metadata

        Returns:
            Log ID
        """
        error_type = None
        stack_trace = None

        if error:
            error_type = type(error).__name__
            stack_trace = traceback.format_exc()

        log = SystemLogCreateDTO(
            service_name=service_name,
            level=SystemLogLevel.ERROR,
            message=message,
            error_type=error_type,
            stack_trace=stack_trace,
            metadata=metadata
        )
        return await self.log_repository.create_log(log)

    async def log_fatal(
        self,
        service_name: str,
        message: str,
        error: Optional[Exception] = None,
        metadata: Optional[dict] = None
    ) -> int:
        """
        Log a FATAL level message

        Args:
            service_name: Service name
            message: Log message
            error: Optional exception
            metadata: Optional metadata

        Returns:
            Log ID
        """
        error_type = None
        stack_trace = None

        if error:
            error_type = type(error).__name__
            stack_trace = traceback.format_exc()

        log = SystemLogCreateDTO(
            service_name=service_name,
            level=SystemLogLevel.FATAL,
            message=message,
            error_type=error_type,
            stack_trace=stack_trace,
            metadata=metadata
        )
        return await self.log_repository.create_log(log)

    async def query_logs(
        self,
        query: SystemLogQueryDTO
    ) -> SystemLogResponseDTO:
        """
        Query system logs with filters

        Args:
            query: Query filters

        Returns:
            Logs matching query
        """
        return await self.log_repository.get_logs(query)

    async def get_log_by_id(
        self,
        log_id: int
    ):
        """
        Get a specific log entry

        Args:
            log_id: Log ID

        Returns:
            Log entry if found
        """
        return await self.log_repository.get_log_by_id(log_id)

    async def get_statistics(
        self,
        service_name: Optional[str] = None
    ) -> list[LogStatsDTO]:
        """
        Get log statistics

        Args:
            service_name: Optional service name filter

        Returns:
            List of statistics per service
        """
        return await self.log_repository.get_stats(service_name)

    async def cleanup_old_logs(
        self,
        days: int = 15
    ) -> int:
        """
        Delete logs older than specified days

        Args:
            days: Number of days to keep (default: 15)

        Returns:
            Number of log files deleted
        """
        return await self.log_repository.delete_old_logs(days)

    async def health_check(self) -> bool:
        """
        Check if logging system is healthy

        Returns:
            True if healthy
        """
        return await self.log_repository.health_check()


class SystemLogger:
    """
    Convenience wrapper for system logging
    Can be used throughout the application
    """

    def __init__(self, log_use_case: SystemLogUseCase):
        self.log_use_case = log_use_case

    async def info(self, service_name: str, message: str, metadata: Optional[dict] = None):
        """Log INFO message"""
        return await self.log_use_case.log_info(service_name, message, metadata)

    async def warning(self, service_name: str, message: str, metadata: Optional[dict] = None):
        """Log WARNING message"""
        return await self.log_use_case.log_warning(service_name, message, metadata)

    async def error(
        self,
        service_name: str,
        message: str,
        error: Optional[Exception] = None,
        metadata: Optional[dict] = None
    ):
        """Log ERROR message"""
        return await self.log_use_case.log_error(service_name, message, error, metadata)

    async def fatal(
        self,
        service_name: str,
        message: str,
        error: Optional[Exception] = None,
        metadata: Optional[dict] = None
    ):
        """Log FATAL message"""
        return await self.log_use_case.log_fatal(service_name, message, error, metadata)

