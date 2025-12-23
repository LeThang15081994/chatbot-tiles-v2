"""
Main Application Settings
Aggregates all configuration settings
"""
from pydantic_settings import BaseSettings
from app.src.infrastructure.config.milvus_settings import MilvusSettings
from app.src.infrastructure.config.redis_settings import RedisSettings
from app.src.infrastructure.config.llm_settings import LLMSettings
from app.src.infrastructure.config.langfuse_settings import LangfuseSettings
from app.src.infrastructure.config.guardrails_settings import GuardrailsSettings
from app.src.infrastructure.config.embedding_settings import EmbeddingSettings
from app.src.infrastructure.config.database_settings import DatabaseSettings


class Settings(BaseSettings):
    """
    Main application settings

    Aggregates all configuration from different services
    """

    # Application
    APP_NAME: str = "chatbot-tiles-v2"
    APP_VERSION: str = "2.0.0"
    APP_ENVIRONMENT: str = "development"
    APP_PORT: int = 8000
    API_V1_STR: str = "/api/v1"

    # Product Base URL
    PRODUCT_BASE_URL: str = "https://gach.ai"

    # File Logging Settings
    LOG_DIR: str = "/app/logging"
    LOG_RETENTION_DAYS: int = 15

    # Component Settings
    milvus: MilvusSettings = MilvusSettings()
    redis: RedisSettings = RedisSettings()
    llm: LLMSettings = LLMSettings()
    langfuse: LangfuseSettings = LangfuseSettings()
    guardrails: GuardrailsSettings = GuardrailsSettings()
    embedding: EmbeddingSettings = EmbeddingSettings()
    database: DatabaseSettings = DatabaseSettings()

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()

