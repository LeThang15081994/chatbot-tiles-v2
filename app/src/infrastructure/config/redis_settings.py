"""
Redis Configuration Settings
"""
from typing import Optional
from pydantic_settings import BaseSettings


class RedisSettings(BaseSettings):
    """Redis configuration"""

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DEFAULT_TTL: int = 900 # 15 minutes

    class Config:
        env_file = ".env"
        case_sensitive = True

