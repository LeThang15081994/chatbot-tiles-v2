"""
Langfuse Configuration Settings
"""
from pydantic_settings import BaseSettings


class LangfuseSettings(BaseSettings):
    """Langfuse configuration"""

    LANGFUSE_PUBLIC_KEY: str = ""
    LANGFUSE_SECRET_KEY: str = ""
    LANGFUSE_HOST: str = "https://cloud.langfuse.com"
    ENVIRONMENT: str = "production"

    class Config:
        env_file = ".env"
        case_sensitive = True

