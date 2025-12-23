"""
File-based System Log Repository Implementation

Application logs được ghi ra file và KHÔNG lưu vào PostgreSQL theo thiết kế.
Hệ thống logging này sử dụng file rotation theo ngày và tự động xóa log cũ hơn 15 ngày.
"""
import logging
import logging.handlers
import os
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta
from app.src.application.interfaces.system_log_repository import ISystemLogRepository
from app.src.application.dto.system_log_dto import (
    SystemLogCreateDTO,
    SystemLogDTO,
    SystemLogQueryDTO,
    SystemLogResponseDTO,
    SystemLogLevel,
    LogStatsDTO,
)

from app.src.infrastructure.config.settings import settings


class FileLogRepository(ISystemLogRepository):
    """
    File-based implementation of system log repository

    Responsibilities:
    - Write logs to daily rotating files (app-YYYY-MM-DD.log)
    - Automatically clean up logs older than 15 days
    - Provide structured logging with ISO 8601 timestamps
    """

    def __init__(
        self,
        log_dir: Optional[str] = None,
        retention_days: Optional[int] = None,
        service_name: Optional[str] = None,
        environment: Optional[str] = None
    ):
        """
        Initialize file log repository

        Args:
            log_dir: Directory to store log files (default: from settings.LOG_DIR)
            retention_days: Number of days to keep logs (default: from settings.LOG_RETENTION_DAYS)
            service_name: Default service name for logs (default: from settings.APP_NAME)
            environment: Application environment (default: from settings.APP_ENVIRONMENT)
        """
        # Use settings if not provided (lazy evaluation to avoid import issues)
        try:
            self.log_dir = Path(log_dir if log_dir is not None else settings.LOG_DIR)
            self.retention_days = retention_days if retention_days is not None else settings.LOG_RETENTION_DAYS
            self.service_name = service_name if service_name is not None else settings.APP_NAME
            self.environment = environment if environment is not None else settings.APP_ENVIRONMENT
        except Exception as e:
            # Fallback values if settings are not available
            self.log_dir = Path(log_dir if log_dir is not None else "/app/logging")
            self.retention_days = retention_days if retention_days is not None else 15
            self.service_name = service_name if service_name is not None else "chatbot"
            self.environment = environment if environment is not None else "development"
            print(f"Warning: Could not load settings, using defaults. Error: {e}")

        # Create log directory if it doesn't exist
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            # If we can't create the directory, try to use a fallback location
            fallback_dir = Path("/tmp/logs")
            print(f"Warning: Could not create log directory {self.log_dir}: {e}")
            print(f"Using fallback directory: {fallback_dir}")
            try:
                fallback_dir.mkdir(parents=True, exist_ok=True)
                self.log_dir = fallback_dir
            except Exception as fallback_error:
                print(f"Error: Could not create fallback log directory: {fallback_error}")
                raise

        # Store current date to track rotation
        self._current_date = datetime.now().date()

        # Get today's log file path (format: app-YYYY-MM-DD.log)
        self._current_log_file = self._get_log_file_path()

        # Create formatter
        formatter = logging.Formatter(
            fmt='%(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Create file handler for today's log file
        handler = logging.FileHandler(
            filename=str(self._current_log_file),
            mode='a',
            encoding='utf-8'
        )
        handler.setFormatter(formatter)

        # Configure root logger
        self.logger = logging.getLogger(f"app.{service_name}")
        self.logger.setLevel(logging.DEBUG)

        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()
        self.logger.addHandler(handler)

        # Prevent duplicate logs
        self.logger.propagate = False

        # Clean up old log files on initialization
        self._cleanup_old_logs()

        # Schedule periodic cleanup (runs daily at startup check)
        self._last_cleanup_date = datetime.now().date()

    def _get_log_file_path(self, date: Optional[datetime] = None) -> Path:
        """
        Get log file path for a specific date

        Args:
            date: Date for log file (default: today)

        Returns:
            Path to log file
        """
        if date is None:
            date = datetime.now()
        date_str = date.strftime("%Y-%m-%d")
        return self.log_dir / f"app-{date_str}.log"

    def _format_log_entry(
        self,
        level: SystemLogLevel,
        message: str,
        service_name: str,
        error_type: Optional[str] = None,
        stack_trace: Optional[str] = None,
        metadata: Optional[dict] = None,
        request_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> str:
        """
        Format log entry as structured text

        Args:
            level: Log level
            message: Log message
            service_name: Service name
            error_type: Error type if any
            stack_trace: Stack trace if any
            metadata: Additional metadata
            request_id: Request ID if available
            user_id: User ID if available

        Returns:
            Formatted log string
        """
        timestamp = datetime.now().isoformat()

        # Build log entry
        parts = [
            f"timestamp={timestamp}",
            f"level={level.value}",
            f"service_name={service_name}",
            f"environment={self.environment}"
        ]

        if request_id:
            parts.append(f"request_id={request_id}")
        if user_id:
            parts.append(f"user_id={user_id}")
        if error_type:
            parts.append(f"error_type={error_type}")

        parts.append(f"message={message}")

        if metadata:
            metadata_str = json.dumps(metadata, ensure_ascii=False)
            parts.append(f"metadata={metadata_str}")

        if stack_trace:
            parts.append(f"stack_trace={stack_trace}")

        return " | ".join(parts)

    def _ensure_current_log_file(self):
        """
        Ensure we're writing to today's log file.
        Rotates to a new file if the date has changed.
        """
        today = datetime.now().date()
        if today != self._current_date:
            # Date changed, rotate to new file
            self._current_date = today
            self._current_log_file = self._get_log_file_path()

            # Create new handler for today's file
            handler = logging.FileHandler(
                filename=str(self._current_log_file),
                mode='a',
                encoding='utf-8'
            )
            handler.setFormatter(logging.Formatter(fmt='%(message)s'))

            # Replace handler
            self.logger.handlers.clear()
            self.logger.addHandler(handler)

            # Clean up old logs when date changes
            if today != self._last_cleanup_date:
                self._cleanup_old_logs()
                self._last_cleanup_date = today

    async def create_log(
        self,
        log: SystemLogCreateDTO
    ) -> int:
        """
        Create a system log entry in file

        Application logs được ghi ra file và KHÔNG lưu vào PostgreSQL theo thiết kế.

        Args:
            log: Log data to create

        Returns:
            Log sequence number (not database ID)
        """
        # Ensure we're writing to today's log file (rotate if needed)
        self._ensure_current_log_file()

        # Extract request_id and user_id from metadata if available
        request_id = None
        user_id = None
        if log.metadata:
            request_id = log.metadata.get("request_id")
            user_id = log.metadata.get("user_id")

        # Format log entry
        log_entry = self._format_log_entry(
            level=log.level,
            message=log.message,
            service_name=log.service_name,
            error_type=log.error_type,
            stack_trace=log.stack_trace,
            metadata=log.metadata,
            request_id=request_id,
            user_id=user_id
        )

        # Write to appropriate log level
        if log.level == SystemLogLevel.INFO:
            self.logger.info(log_entry)
        elif log.level == SystemLogLevel.WARN:
            self.logger.warning(log_entry)
        elif log.level == SystemLogLevel.ERROR:
            self.logger.error(log_entry)
        elif log.level == SystemLogLevel.FATAL:
            self.logger.critical(log_entry)
        else:
            self.logger.debug(log_entry)

        # Return a sequence number (not database ID since we're not using DB)
        # This is just for compatibility with the interface
        return hash(f"{datetime.now().isoformat()}{log.message}") % 1000000

    async def get_logs(
        self,
        query: SystemLogQueryDTO
    ) -> SystemLogResponseDTO:
        """
        Query system logs from files

        Note: This is a simplified implementation. For production,
        consider using log aggregation tools like ELK, Loki, etc.

        Args:
            query: Query filters

        Returns:
            Logs matching query (limited functionality for file-based logs)
        """
        # For file-based logging, querying is limited
        # In production, use log aggregation tools
        logs = []
        total_count = 0

        # Try to read from today's log file
        today_file = self._get_log_file_path()
        if today_file.exists():
            try:
                with open(today_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    total_count = len(lines)
                    # Simple filtering (for production, use proper log parsing)
                    for line in lines[-query.limit:]:
                        if query.service_name and query.service_name not in line:
                            continue
                        if query.level and query.level.value not in line:
                            continue
                        if query.search_text and query.search_text.lower() not in line.lower():
                            continue

                        # Create a simplified DTO (file-based logs don't have IDs)
                        log_dto = SystemLogDTO(
                            id=hash(line) % 1000000,
                            service_name=query.service_name or self.service_name,
                            level=query.level or SystemLogLevel.INFO,
                            message=line.strip(),
                            error_type=None,
                            stack_trace=None,
                            metadata=None,
                            created_at=datetime.now()
                        )
                        logs.append(log_dto)
            except Exception:
                pass

        return SystemLogResponseDTO(
            logs=logs,
            total_count=total_count,
            page_size=len(logs),
            offset=query.offset
        )

    async def get_log_by_id(
        self,
        log_id: int
    ) -> Optional[SystemLogDTO]:
        """
        Get a specific log entry by ID

        Note: File-based logs don't have persistent IDs.
        This method is kept for interface compatibility.

        Args:
            log_id: Log ID (not applicable for file-based logs)

        Returns:
            None (file-based logs don't support ID-based retrieval)
        """
        # File-based logs don't have persistent IDs
        return None

    async def get_stats(
        self,
        service_name: Optional[str] = None
    ) -> List[LogStatsDTO]:
        """
        Get log statistics from files

        Args:
            service_name: Optional service name filter

        Returns:
            List of statistics per service
        """
        stats = {
            "total_logs": 0,
            "info_count": 0,
            "warn_count": 0,
            "error_count": 0,
            "fatal_count": 0,
            "last_error": None,
            "last_fatal": None
        }

        # Count logs in today's file
        today_file = self._get_log_file_path()
        if today_file.exists():
            try:
                with open(today_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        stats["total_logs"] += 1
                        if "level=INFO" in line:
                            stats["info_count"] += 1
                        elif "level=WARN" in line:
                            stats["warn_count"] += 1
                        elif "level=ERROR" in line:
                            stats["error_count"] += 1
                            stats["last_error"] = datetime.now()
                        elif "level=FATAL" in line:
                            stats["fatal_count"] += 1
                            stats["last_fatal"] = datetime.now()
            except Exception:
                pass

        return [LogStatsDTO(
            service_name=service_name or self.service_name,
            total_logs=stats["total_logs"],
            info_count=stats["info_count"],
            warn_count=stats["warn_count"],
            error_count=stats["error_count"],
            fatal_count=stats["fatal_count"],
            last_error=stats["last_error"],
            last_fatal=stats["last_fatal"]
        )]

    async def delete_old_logs(
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
        return self._cleanup_old_logs(days)

    def _cleanup_old_logs(self, days: Optional[int] = None) -> int:
        """
        Internal method to clean up old log files

        Args:
            days: Number of days to keep (default: self.retention_days)

        Returns:
            Number of files deleted
        """
        if days is None:
            days = self.retention_days

        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0

        # Clean up old log files
        if self.log_dir.exists():
            for log_file in self.log_dir.glob("app-*.log*"):
                try:
                    # Extract date from filename
                    # Format: app-YYYY-MM-DD.log or app.log.YYYY-MM-DD
                    file_date = None
                    if log_file.name.startswith("app-") and log_file.name.endswith(".log"):
                        date_str = log_file.name.replace("app-", "").replace(".log", "")
                        try:
                            file_date = datetime.strptime(date_str, "%Y-%m-%d")
                        except ValueError:
                            continue
                    elif ".log." in log_file.name:
                        # Handle rotated files: app.log.2025-01-15
                        date_str = log_file.name.split(".log.")[-1]
                        try:
                            file_date = datetime.strptime(date_str, "%Y-%m-%d")
                        except ValueError:
                            continue

                    if file_date and file_date.date() < cutoff_date.date():
                        try:
                            log_file.unlink()
                            deleted_count += 1
                        except Exception:
                            # Ignore errors during file deletion
                            pass
                except Exception:
                    # Ignore errors during cleanup
                    pass

        return deleted_count

    async def health_check(self) -> bool:
        """
        Check if logging system is healthy

        Returns:
            True if log directory is writable
        """
        try:
            # Check if we can write to log directory
            test_file = self.log_dir / ".health_check"
            test_file.write_text("test")
            test_file.unlink()
            return True
        except Exception:
            return False

