  # System Logging với PostgreSQL - Setup Guide

## 📋 Tổng quan

Hệ thống logging đã được implement theo **Clean Architecture** với các tính năng:

✅ Log critical events vào PostgreSQL (dbo.system_logs)
✅ Multiple log levels: INFO, WARN, ERROR, FATAL
✅ Structured logging với metadata (JSONB)
✅ Query và analytics APIs
✅ Automatic log retention management
✅ Production-ready với connection pooling

---

## 🏗️ Kiến trúc

```
Application Layer (Use Cases)
    ↓
    SystemLogUseCase
    ↓
    ISystemLogRepository (Interface)
    ↓
Infrastructure Layer
    ↓
    SystemLogRepository (PostgreSQL)
    ↓
    PostgreSQLDatabase (Connection Pool)
    ↓
    dbo.system_logs table
```

---

## 📦 Files đã tạo

### 1. Application Layer

```
src/application/
├── dto/
│   └── system_log_dto.py          # DTOs cho logging
├── interfaces/
│   └── system_log_repository.py   # Repository interface
└── use_cases/
    └── system_log_use_case.py     # Business logic
```

### 2. Infrastructure Layer

```
src/infrastructure/
├── postgresql/
│   ├── __init__.py
│   ├── database.py                # Connection pool manager
│   └── system_log_repository.py  # PostgreSQL implementation
└── config/
    └── database_settings.py       # Database configuration
```

---

## 🚀 Setup Instructions

### Step 1: Environment Variables

Tạo hoặc update file `.env`:

```bash
# PostgreSQL Connection
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=gachai_db
POSTGRES_USER=gachai_db
POSTGRES_PASSWORD=your_secure_password

# Connection Pool
POSTGRES_MIN_POOL_SIZE=5
POSTGRES_MAX_POOL_SIZE=20

# Logging Settings
ENABLE_DATABASE_LOGGING=True
LOG_RETENTION_DAYS=30
```

### Step 2: Install Dependencies

```bash
pip install asyncpg pydantic-settings
```

### Step 3: Database Setup

Database và table đã được tạo qua init scripts:
- `db/postgresql/initdb/01-create-user.sql`
- `db/postgresql/initdb/02-create-system-logs.sql`

Table schema:
```sql
CREATE TABLE dbo.system_logs (
    id BIGSERIAL PRIMARY KEY,
    service_name TEXT NOT NULL,
    level TEXT NOT NULL CHECK (level IN ('INFO', 'WARN', 'ERROR', 'FATAL')),
    message TEXT NOT NULL,
    error_type TEXT,
    stack_trace TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT now()
);
```

---

## 💻 Usage Examples

### 1. Basic Setup (trong Bootstrap/DI Container)

```python
from src.infrastructure.postgresql.database import PostgreSQLDatabase
from src.infrastructure.postgresql import SystemLogRepository
from src.application.use_cases import SystemLogUseCase, SystemLogger
from src.infrastructure.config.database_settings import db_settings

# Initialize database
db = PostgreSQLDatabase(
    host=db_settings.POSTGRES_HOST,
    port=db_settings.POSTGRES_PORT,
    database=db_settings.POSTGRES_DB,
    user=db_settings.POSTGRES_USER,
    password=db_settings.POSTGRES_PASSWORD,
    min_size=db_settings.POSTGRES_MIN_POOL_SIZE,
    max_size=db_settings.POSTGRES_MAX_POOL_SIZE
)

# Connect to database
await db.connect()

# Create repository
log_repository = SystemLogRepository(db)

# Create use case
system_log_use_case = SystemLogUseCase(
    log_repository=log_repository,
    service_name="chatbot"  # Default service name
)

# Create convenient logger
system_logger = SystemLogger(system_log_use_case)
```

### 2. Logging trong Use Cases

```python
# src/application/use_cases/rag_use_case.py

class RAGUseCase:
    def __init__(
        self,
        vector_store: IVectorStoreRepository,
        llm_service: ILLMRepository,
        system_logger: SystemLogger  # Inject logger
    ):
        self.vector_store = vector_store
        self.llm_service = llm_service
        self.system_logger = system_logger

    async def process_chat(self, request: ChatRequestDTO):
        try:
            # Log start
            await self.system_logger.info(
                "Chat processing started",
                session_id=request.session_id,
                user_id=request.user_id
            )

            # ... process chat ...

            # Log success
            await self.system_logger.info(
                "Chat processing completed successfully",
                session_id=request.session_id,
                processing_time_ms=processing_time
            )

            return response

        except Exception as e:
            # Log error with full context
            await self.system_logger.error(
                f"Chat processing failed: {str(e)}",
                error=e,
                session_id=request.session_id,
                user_id=request.user_id,
                question=request.question
            )
            raise
```

### 3. Manual Logging với Use Case

```python
# Direct use case methods
from src.application.dto.system_log_dto import SystemLogLevel

# INFO level
await system_log_use_case.log_info(
    message="Service started successfully",
    metadata={"version": "1.0.0", "environment": "production"}
)

# WARN level
await system_log_use_case.log_warn(
    message="High memory usage detected",
    metadata={"memory_usage_mb": 1500, "threshold_mb": 1024}
)

# ERROR level
try:
    # ... code that might fail ...
    pass
except Exception as e:
    await system_log_use_case.log_error(
        message="Failed to connect to LLM service",
        error=e,  # Exception object
        metadata={"model": "groq", "retry_count": 3}
    )

# FATAL level
await system_log_use_case.log_fatal(
    message="Critical system failure",
    error=critical_exception,
    metadata={"component": "database", "action": "shutdown"}
)
```

### 4. Query Logs

```python
from src.application.dto.system_log_dto import (
    SystemLogQueryDTO,
    SystemLogLevel
)
from datetime import datetime, timedelta

# Query logs
query = SystemLogQueryDTO(
    service_name="chatbot",
    level=SystemLogLevel.ERROR,
    start_date=datetime.now() - timedelta(hours=24),
    end_date=datetime.now(),
    search_text="LLM",
    limit=50,
    offset=0
)

result = await system_log_use_case.query_logs(query)

print(f"Found {result.total_count} logs")
for log in result.logs:
    print(f"[{log.level}] {log.created_at}: {log.message}")
```

### 5. Get Statistics

```python
# Get stats for all services
stats = await system_log_use_case.get_stats()

for stat in stats:
    print(f"Service: {stat.service_name}")
    print(f"  Total: {stat.total_logs}")
    print(f"  Errors: {stat.error_count}")
    print(f"  Fatals: {stat.fatal_count}")
    print(f"  Last error: {stat.last_error}")

# Get stats for specific service
chatbot_stats = await system_log_use_case.get_stats(service_name="chatbot")
```

### 6. Cleanup Old Logs (Maintenance Task)

```python
# Delete logs older than 30 days
deleted_count = await system_log_use_case.cleanup_old_logs(
    retention_days=30
)
print(f"Deleted {deleted_count} old logs")
```

---

## 🎯 Best Practices

### 1. **Selective Logging**
Chỉ log vào database cho:
- ✅ Errors và Fatal errors
- ✅ Critical business events
- ✅ Security events
- ✅ Performance issues
- ❌ KHÔNG log debug/verbose logs

### 2. **Structured Metadata**
```python
# ✅ Good - Structured metadata
await logger.error(
    "LLM API call failed",
    error=e,
    model="groq",
    session_id=session_id,
    retry_count=3,
    response_time_ms=1500
)

# ❌ Bad - All in message
await logger.error(
    f"LLM API call failed for model groq, session {session_id}, retry 3"
)
```

### 3. **Error Handling**
```python
# SystemLogger silently catches exceptions to not break app
await system_logger.error("Something failed", error=e)

# Use case methods raise exceptions if you need to handle them
try:
    await system_log_use_case.log_error("Error", error=e)
except Exception as log_error:
    # Handle logging failure
    pass
```

### 4. **Service Names**
Use consistent service names:
- `chatbot` - Main chatbot service
- `image-search` - Image search service
- `api` - API gateway
- `admin` - Admin panel

---

## 📊 Monitoring Dashboard

### Query Examples

**Get error rate per hour:**
```sql
SELECT
    date_trunc('hour', created_at) as hour,
    service_name,
    COUNT(*) FILTER (WHERE level = 'ERROR') as error_count,
    COUNT(*) FILTER (WHERE level = 'FATAL') as fatal_count
FROM dbo.system_logs
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY hour, service_name
ORDER BY hour DESC;
```

**Get top error types:**
```sql
SELECT
    error_type,
    COUNT(*) as count,
    MAX(created_at) as last_occurrence
FROM dbo.system_logs
WHERE level IN ('ERROR', 'FATAL')
    AND created_at >= NOW() - INTERVAL '7 days'
GROUP BY error_type
ORDER BY count DESC
LIMIT 10;
```

**Get recent critical errors:**
```sql
SELECT
    created_at,
    service_name,
    level,
    message,
    metadata
FROM dbo.system_logs
WHERE level IN ('ERROR', 'FATAL')
ORDER BY created_at DESC
LIMIT 20;
```

---

## 🔧 Maintenance

### Automatic Cleanup (Scheduled Task)

```python
# Run daily via cron/scheduler
async def daily_maintenance():
    """Daily log maintenance task"""
    # Cleanup old logs
    deleted = await system_log_use_case.cleanup_old_logs(
        retention_days=30
    )

    # Log the cleanup
    await system_logger.info(
        f"Log maintenance completed",
        deleted_count=deleted
    )
```

### Manual Cleanup

```sql
-- Delete logs older than 30 days
DELETE FROM dbo.system_logs
WHERE created_at < NOW() - INTERVAL '30 days';

-- Vacuum to reclaim space
VACUUM ANALYZE dbo.system_logs;
```

---

## ✅ Testing

```python
# Test logging
async def test_logging():
    # Test INFO
    log_id = await system_logger.info("Test info log")
    assert log_id > 0

    # Test ERROR with exception
    try:
        raise ValueError("Test error")
    except Exception as e:
        await system_logger.error("Test error log", error=e)

    # Query logs
    query = SystemLogQueryDTO(limit=10)
    result = await system_log_use_case.query_logs(query)
    assert len(result.logs) > 0
```

---

## 🎉 Summary

✅ **System logging hoàn chỉnh và production-ready**
✅ **Clean Architecture compliance**
✅ **Easy to use với SystemLogger wrapper**
✅ **Scalable với connection pooling**
✅ **Queryable và analytics-ready**
✅ **Automatic maintenance với cleanup**

Hệ thống đã sẵn sàng để deploy! 🚀

