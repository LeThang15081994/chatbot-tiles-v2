"""
System Log Repository Implementation for PostgreSQL
"""
import json
from typing import List, Optional
from datetime import datetime, timedelta
from ...application.interfaces.system_log_repository import ISystemLogRepository
from ...application.dto.system_log_dto import (
    SystemLogCreateDTO,
    SystemLogDTO,
    SystemLogQueryDTO,
    SystemLogResponseDTO,
    SystemLogLevel,
    LogStatsDTO,
)
from .database import PostgreSQLDatabase


class SystemLogRepository(ISystemLogRepository):
    """
    PostgreSQL implementation of system log repository
    Logs to dbo.system_logs table
    """

    def __init__(self, database: PostgreSQLDatabase):
        """
        Initialize repository

        Args:
            database: PostgreSQL database manager
        """
        self.db = database

    async def create_log(
        self,
        log: SystemLogCreateDTO
    ) -> int:
        """Create a system log entry"""
        query = """
            INSERT INTO dbo.system_logs (
                service_name, level, message, error_type, stack_trace, metadata, created_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, now())
            RETURNING id
        """

        # Convert metadata to JSON string
        metadata_json = json.dumps(log.metadata) if log.metadata else None

        log_id = await self.db.fetchval(
            query,
            log.service_name,
            log.level.value,
            log.message,
            log.error_type,
            log.stack_trace,
            metadata_json
        )

        return log_id

    async def get_logs(
        self,
        query: SystemLogQueryDTO
    ) -> SystemLogResponseDTO:
        """Query system logs with filters"""
        # Build WHERE clause
        conditions = []
        params = []
        param_counter = 1

        if query.service_name:
            conditions.append(f"service_name = ${param_counter}")
            params.append(query.service_name)
            param_counter += 1

        if query.level:
            conditions.append(f"level = ${param_counter}")
            params.append(query.level.value)
            param_counter += 1

        if query.start_date:
            conditions.append(f"created_at >= ${param_counter}")
            params.append(query.start_date)
            param_counter += 1

        if query.end_date:
            conditions.append(f"created_at <= ${param_counter}")
            params.append(query.end_date)
            param_counter += 1

        if query.search_text:
            conditions.append(f"message ILIKE ${param_counter}")
            params.append(f"%{query.search_text}%")
            param_counter += 1

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Get total count
        count_query = f"""
            SELECT COUNT(*)
            FROM dbo.system_logs
            WHERE {where_clause}
        """
        total_count = await self.db.fetchval(count_query, *params)

        # Get logs
        logs_query = f"""
            SELECT id, service_name, level, message, error_type, stack_trace, metadata, created_at
            FROM dbo.system_logs
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_counter} OFFSET ${param_counter + 1}
        """
        params.extend([query.limit, query.offset])

        rows = await self.db.fetch(logs_query, *params)

        # Convert to DTOs
        logs = []
        for row in rows:
            metadata = json.loads(row['metadata']) if row['metadata'] else None

            log_dto = SystemLogDTO(
                id=row['id'],
                service_name=row['service_name'],
                level=SystemLogLevel(row['level']),
                message=row['message'],
                error_type=row['error_type'],
                stack_trace=row['stack_trace'],
                metadata=metadata,
                created_at=row['created_at']
            )
            logs.append(log_dto)

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
        """Get a specific log entry by ID"""
        query = """
            SELECT id, service_name, level, message, error_type, stack_trace, metadata, created_at
            FROM dbo.system_logs
            WHERE id = $1
        """

        row = await self.db.fetchrow(query, log_id)

        if not row:
            return None

        metadata = json.loads(row['metadata']) if row['metadata'] else None

        return SystemLogDTO(
            id=row['id'],
            service_name=row['service_name'],
            level=SystemLogLevel(row['level']),
            message=row['message'],
            error_type=row['error_type'],
            stack_trace=row['stack_trace'],
            metadata=metadata,
            created_at=row['created_at']
        )

    async def get_stats(
        self,
        service_name: Optional[str] = None
    ) -> List[LogStatsDTO]:
        """Get log statistics by service"""
        where_clause = "WHERE service_name = $1" if service_name else ""
        params = [service_name] if service_name else []

        query = f"""
            SELECT
                service_name,
                COUNT(*) as total_logs,
                COUNT(*) FILTER (WHERE level = 'INFO') as info_count,
                COUNT(*) FILTER (WHERE level = 'WARN') as warn_count,
                COUNT(*) FILTER (WHERE level = 'ERROR') as error_count,
                COUNT(*) FILTER (WHERE level = 'FATAL') as fatal_count,
                MAX(created_at) FILTER (WHERE level = 'ERROR') as last_error,
                MAX(created_at) FILTER (WHERE level = 'FATAL') as last_fatal
            FROM dbo.system_logs
            {where_clause}
            GROUP BY service_name
            ORDER BY service_name
        """

        rows = await self.db.fetch(query, *params)

        stats = []
        for row in rows:
            stat = LogStatsDTO(
                service_name=row['service_name'],
                total_logs=row['total_logs'],
                info_count=row['info_count'] or 0,
                warn_count=row['warn_count'] or 0,
                error_count=row['error_count'] or 0,
                fatal_count=row['fatal_count'] or 0,
                last_error=row['last_error'],
                last_fatal=row['last_fatal']
            )
            stats.append(stat)

        return stats

    async def delete_old_logs(
        self,
        days: int = 30
    ) -> int:
        """Delete logs older than specified days"""
        cutoff_date = datetime.now() - timedelta(days=days)

        query = """
            DELETE FROM dbo.system_logs
            WHERE created_at < $1
        """

        result = await self.db.execute(query, cutoff_date)

        # Extract number of deleted rows from result string
        # Result format: "DELETE N"
        deleted_count = int(result.split()[-1]) if result else 0

        return deleted_count

    async def health_check(self) -> bool:
        """Check if logging system is healthy"""
        try:
            await self.db.fetchval("SELECT 1 FROM dbo.system_logs LIMIT 1")
            return True
        except Exception:
            return False

