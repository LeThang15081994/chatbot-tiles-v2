"""
Logging Repository

Centralized logging configuration and repository implementation with:
- Daily rotation (app-YYYY-MM-DD.log)
- 15-day retention
- Structured logging
- Multiple log levels
- ISystemLogRepository implementation
"""
import logging
import logging.handlers
import sys
import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timedelta

from app.src.infrastructure.config.settings import settings
from app.src.application.interfaces.repositories.system_log_repository import ISystemLogRepository
from app.src.application.dto.system_log_dto import (
    SystemLogCreateDTO,
    SystemLogDTO,
    SystemLogQueryDTO,
    SystemLogResponseDTO,
    SystemLogLevel,
    LogStatsDTO,
)


class LoggerConfig:
    """
    Centralized logging configuration

    Features:
    - Daily log rotation (app-YYYY-MM-DD.log)
    - Automatic cleanup of logs older than 15 days
    - Structured logging with JSON-like format
    - Console and file handlers
    """

    _configured = False
    _log_dir: Optional[Path] = None

    @classmethod
    def setup_logging(
        cls,
        log_dir: Optional[str] = None,
        retention_days: int = 15,
        log_level: str = "INFO",
        service_name: str = "chatbot"
    ) -> None:
        """
        Setup application-wide logging configuration

        Args:
            log_dir: Directory for log files (default: app/logging)
            retention_days: Number of days to keep logs (default: 15)
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            service_name: Service name for log identification
        """
        if cls._configured:
            return  # Already configured

        # Determine log directory
        if log_dir is None:
            try:
                log_dir = settings.LOG_DIR if hasattr(settings, 'LOG_DIR') else "./app/logging"
            except Exception:
                log_dir = "./app/logging"

        cls._log_dir = Path(log_dir)
        cls._log_dir.mkdir(parents=True, exist_ok=True)

        # Convert log level string to logging constant
        level = getattr(logging, log_level.upper(), logging.INFO)

        # Create formatter with structured format
        formatter = logging.Formatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Create daily rotating file handler
        log_file = cls._log_dir / f"app-{datetime.now().strftime('%Y-%m-%d')}.log"
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=str(log_file),
            when='midnight',
            interval=1,
            backupCount=retention_days,
            encoding='utf-8',
            delay=False
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        file_handler.suffix = "%Y-%m-%d"

        # Create console handler (for development)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        # Remove existing handlers to avoid duplicates
        root_logger.handlers.clear()

        # Add handlers
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

        # Prevent duplicate logs from propagating
        root_logger.propagate = False

        # Clean up old log files
        cls._cleanup_old_logs(cls._log_dir, retention_days)

        cls._configured = True

        # Log configuration success
        logger = logging.getLogger(__name__)
        logger.info(f"Logging configured: dir={log_dir}, level={log_level}, retention={retention_days} days")

    @staticmethod
    def _cleanup_old_logs(log_dir: Path, retention_days: int) -> None:
        """
        Clean up log files older than retention_days

        Args:
            log_dir: Log directory
            retention_days: Number of days to keep
        """
        if not log_dir.exists():
            return

        cutoff_date = datetime.now() - timedelta(days=retention_days)
        deleted_count = 0

        for log_file in log_dir.glob("app-*.log*"):
            try:
                # Extract date from filename: app-YYYY-MM-DD.log
                if log_file.name.startswith("app-") and log_file.name.endswith(".log"):
                    date_str = log_file.name.replace("app-", "").replace(".log", "")
                    try:
                        file_date = datetime.strptime(date_str, "%Y-%m-%d")
                        if file_date.date() < cutoff_date.date():
                            log_file.unlink()
                            deleted_count += 1
                    except ValueError:
                        # Skip files with invalid date format
                        continue
            except Exception:
                # Ignore errors during cleanup
                pass

        if deleted_count > 0:
            logger = logging.getLogger(__name__)
            logger.info(f"Cleaned up {deleted_count} old log file(s)")

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get a logger instance for a module

        Args:
            name: Logger name (usually __name__)

        Returns:
            Configured logger instance
        """
        if not cls._configured:
            # Auto-configure if not already done
            cls.setup_logging()

        return logging.getLogger(name)


class LoggerRepository(ISystemLogRepository):
    """
    Logger Repository Implementation

    Implements ISystemLogRepository interface using the centralized logging system.
    Uses the same log files as LoggerConfig (app-YYYY-MM-DD.log).
    """

    def __init__(
        self,
        log_dir: Optional[str] = None,
        retention_days: Optional[int] = None,
        service_name: Optional[str] = None,
        environment: Optional[str] = None
    ):
        """
        Initialize logger repository

        Args:
            log_dir: Directory for log files (default: from settings)
            retention_days: Number of days to keep logs (default: 15)
            service_name: Default service name for logs
            environment: Application environment
        """
        # Use settings if not provided
        try:
            self.log_dir = Path(log_dir if log_dir is not None else settings.LOG_DIR)
            self.retention_days = retention_days if retention_days is not None else settings.LOG_RETENTION_DAYS
            self.service_name = service_name if service_name is not None else settings.APP_NAME
            self.environment = environment if environment is not None else settings.APP_ENVIRONMENT
        except Exception:
            # Fallback values
            self.log_dir = Path(log_dir if log_dir is not None else "./app/logging")
            self.retention_days = retention_days if retention_days is not None else 15
            self.service_name = service_name if service_name is not None else "chatbot"
            self.environment = environment if environment is not None else "development"

        # Create log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Store current date to track rotation
        self._current_date = datetime.now().date()
        self._current_log_file = self._get_log_file_path()

        # Clean up old log files on initialization
        self._cleanup_old_logs()

        # Schedule periodic cleanup
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

        Args:
            log: Log data to create

        Returns:
            Log sequence number
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

        # Write directly to file to maintain structured format
        try:
            with open(self._current_log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry + '\n')
        except Exception:
            # Fallback: use root logger if file write fails
            root_logger = logging.getLogger()
            if log.level == SystemLogLevel.INFO:
                root_logger.info(log_entry)
            elif log.level == SystemLogLevel.WARN:
                root_logger.warning(log_entry)
            elif log.level == SystemLogLevel.ERROR:
                root_logger.error(log_entry)
            elif log.level == SystemLogLevel.FATAL:
                root_logger.critical(log_entry)
            else:
                root_logger.debug(log_entry)

        # Return a sequence number
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
            Logs matching query
        """
        logs = []
        total_count = 0

        # Try to read from today's log file
        today_file = self._get_log_file_path()
        if today_file.exists():
            try:
                with open(today_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    total_count = len(lines)
                    # Simple filtering
                    for line in lines[-query.limit:]:
                        if query.service_name and query.service_name not in line:
                            continue
                        if query.level and query.level.value not in line:
                            continue
                        if query.search_text and query.search_text.lower() not in line.lower():
                            continue

                        # Create a simplified DTO
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
            log_id: Log ID

        Returns:
            None (file-based logs don't support ID-based retrieval)
        """
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
                    # Extract date from filename: app-YYYY-MM-DD.log
                    if log_file.name.startswith("app-") and log_file.name.endswith(".log"):
                        date_str = log_file.name.replace("app-", "").replace(".log", "")
                        try:
                            file_date = datetime.strptime(date_str, "%Y-%m-%d")
                            if file_date.date() < cutoff_date.date():
                                log_file.unlink()
                                deleted_count += 1
                        except ValueError:
                            continue
                except Exception:
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


def setup_app_logging() -> None:
    """
    Convenience function to setup application logging

    Call this at application startup (e.g., in main.py or container.py)
    """
    try:
        log_dir = settings.LOG_DIR if hasattr(settings, 'LOG_DIR') else "./app/logging"
        retention_days = settings.LOG_RETENTION_DAYS if hasattr(settings, 'LOG_RETENTION_DAYS') else 15
        log_level = settings.LOG_LEVEL if hasattr(settings, 'LOG_LEVEL') else "INFO"
        service_name = settings.APP_NAME if hasattr(settings, 'APP_NAME') else "chatbot"

        LoggerConfig.setup_logging(
            log_dir=log_dir,
            retention_days=retention_days,
            log_level=log_level,
            service_name=service_name
        )
    except Exception as e:
        # Fallback configuration if settings are not available
        LoggerConfig.setup_logging(
            log_dir="./app/logging",
            retention_days=15,
            log_level="INFO",
            service_name="chatbot"
        )
        logger = logging.getLogger(__name__)
        logger.warning(f"Could not load logging settings, using defaults. Error: {e}")

