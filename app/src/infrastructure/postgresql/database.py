"""
PostgreSQL Database Connection Manager
"""
import asyncpg
from typing import Optional
from contextlib import asynccontextmanager

from app.src.infrastructure.config.database_settings import db_settings

class PostgreSQLDatabase:
    """
    PostgreSQL connection pool manager
    Handles connection pooling and query execution
    """

    def __init__(
        self,
        host: str = db_settings.POSTGRES_HOST,
        port: int = db_settings.POSTGRES_PORT,
        database: str = db_settings.POSTGRES_DB,
        user: str = db_settings.POSTGRES_USER,
        password: str = db_settings.POSTGRES_PASSWORD,
        min_size: int = 5,
        max_size: int = 20
    ):
        """
        Initialize database manager

        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password
            min_size: Minimum pool size
            max_size: Maximum pool size
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.min_size = min_size
        self.max_size = max_size
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Create connection pool"""
        if self.pool is None:
            self.pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                min_size=self.min_size,
                max_size=self.max_size,
                command_timeout=30
            )

    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            self.pool = None

    @asynccontextmanager
    async def acquire(self):
        """
        Acquire a connection from pool

        Usage:
            async with db.acquire() as conn:
                result = await conn.fetch("SELECT * FROM table")
        """
        if self.pool is None:
            await self.connect()

        async with self.pool.acquire() as connection:
            yield connection

    async def execute(self, query: str, *args):
        """
        Execute a query (INSERT, UPDATE, DELETE)

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            Execution result
        """
        async with self.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args):
        """
        Fetch multiple rows

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            List of records
        """
        async with self.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        """
        Fetch single row

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            Single record or None
        """
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args):
        """
        Fetch single value

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            Single value or None
        """
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def health_check(self) -> bool:
        """
        Check database health

        Returns:
            True if database is accessible
        """
        try:
            async with self.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False

