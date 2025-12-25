"""
Database Configuration Settings
"""
import os
from pydantic_settings import BaseSettings
from pydantic import Field


class DatabaseSettings(BaseSettings):
    """PostgreSQL database settings"""

    # PostgreSQL Connection
    POSTGRES_HOST: str = Field(default="localhost", description="PostgreSQL host")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")
    POSTGRES_DB: str = Field(default="gachai_db", description="PostgreSQL database name")
    POSTGRES_USER: str = Field(default="gachai_db", description="PostgreSQL user")
    POSTGRES_PASSWORD: str = Field(default="gachai@123", description="PostgreSQL password")

    # Connection Pool Settings
    POSTGRES_MIN_POOL_SIZE: int = Field(default=5, description="Minimum connection pool size")
    POSTGRES_MAX_POOL_SIZE: int = Field(default=20, description="Maximum connection pool size")

    # Logging Settings
    ENABLE_DATABASE_LOGGING: bool = Field(default=True, description="Enable logging to database")
    LOG_RETENTION_DAYS: int = Field(default=30, description="Number of days to retain logs")

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
db_settings = DatabaseSettings()

