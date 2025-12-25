"""
Langfuse Configuration Settings
"""
from pydantic_settings import BaseSettings
from pydantic import Field

class LangfuseSettings(BaseSettings):
    """Langfuse configuration"""
    LANGFUSE_PUBLIC_KEY: str = Field(default="", description="Langfuse public key")
    LANGFUSE_SECRET_KEY: str = Field(default="", description="Langfuse secret key")
    LANGFUSE_HOST: str = Field(default="https://cloud.langfuse.com", description="Langfuse host")
    ENVIRONMENT: str = Field(default="production", description="Langfuse environment")

    class Config:
        env_file = ".env"
        case_sensitive = True

