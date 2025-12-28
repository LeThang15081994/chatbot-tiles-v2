"""
Application Configuration Settings
All settings consolidated in one file for easier management
Combines Pydantic Settings with os.getenv() for loading from .env file
"""
import os
from pathlib import Path
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from dotenv import load_dotenv

# Get the directory containing this settings file
SETTINGS_DIR = Path(__file__).parent

# Load environment variables from .env file in the same directory as settings.py
env_file_path = SETTINGS_DIR / ".env"
load_dotenv(dotenv_path=env_file_path)


class Settings(BaseSettings):
    """
    Main application settings
    Combines Pydantic Settings (auto-loading and validation) with os.getenv() support
    All configuration loaded from .env file
    """
    # ==================== Application Settings ====================
    APP_NAME: str = Field(default="chatbot-tiles-v2", description="Application name")
    APP_VERSION: str = Field(default="2.0.0", description="Application version")
    APP_ENVIRONMENT: str = Field(default="development", description="Application environment")
    APP_PORT: int = Field(default=8000, description="Application port")
    API_V1_STR: str = Field(default="/api/v1", description="API version string")
    PRODUCT_BASE_URL: str = Field(default="https://gach.ai", description="Product base URL")

    # CORS Settings
    ALLOWED_ORIGINS: List[str] = Field(
        default_factory=lambda: ["*"],
        description="Allowed CORS origins (use ['*'] for all in dev)"
    )

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse ALLOWED_ORIGINS from string or list"""
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            return [origin.strip() for origin in v.split(",")]
        return v

    # File Logging Settings
    LOG_DIR: str = Field(default="./app/logging", description="Log directory path")
    LOG_RETENTION_DAYS: int = Field(default=15, description="Number of days to keep logs")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)")

    # ==================== Helper Methods for os.getenv() compatibility ====================
    @classmethod
    def get_env(cls, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Helper method to get environment variable using os.getenv()
        Can be used as alternative to Pydantic's automatic loading
        """
        return os.getenv(key, default)

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get setting value by key, with fallback to os.getenv()
        Useful for dynamic access to settings
        """
        if hasattr(self, key):
            return getattr(self, key)
        return os.getenv(key, default)

    class Config:
        """Pydantic configuration"""
        env_file = str(env_file_path)
        env_file_encoding = "utf-8"
        case_sensitive = True
        # Allow reading from environment variables
        extra = "ignore"


class MilvusSettings(BaseSettings):
    """Milvus vector database settings"""
    MILVUS_HOST: str = Field(default="localhost", description="Milvus IP")
    MILVUS_PORT: int = Field(default=19530, description="Milvus Port")
    MILVUS_ALIAS: str = Field(default="default", description="Milvus Alias")
    MILVUS_DB: str = Field(default="chatbot_gachai", description="Milvus Database Name")
    MILVUS_USER: Optional[str] = Field(default="root", description="Milvus Username")
    MILVUS_PASSWORD: Optional[str] = Field(default="Milvus", description="Milvus Password")
    MILVUS_COLLECTION_COMPANY_DOCUMENT: str = Field(default="company_document_info", description="Milvus Company Document Collection Name")
    MILVUS_COLLECTION_PRODUCTS: str = Field(default="products", description="Milvus Products Collection Name")
    MILVUS_COLLECTION_PRODUCTS_INFO: str = Field(default="products_info", description="Milvus Products Info Collection Name")
    MILVUS_COLLECTION_COLLECTION_INFO: str = Field(default="collection_info", description="Milvus Collection Info Collection Name")
    MILVUS_DIMENSION: int = Field(default=1536, description="Milvus Dimension")
    MILVUS_INDEX_TYPE: str = Field(default="IVF_FLAT", description="Milvus Index Type")
    MILVUS_METRIC_TYPE: str = Field(default="IP", description="Milvus Metric Type")
    MILVUS_NLIST: int = Field(default=128, description="Milvus NList")

    class Config:
        """Pydantic configuration"""
        env_file = str(env_file_path)
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


class RedisSettings(BaseSettings):
    """Redis cache settings"""
    REDIS_HOST: str = Field(default="localhost", description="Redis host")
    REDIS_PORT: int = Field(default=6379, description="Redis port")
    REDIS_DB: int = Field(default=0, description="Redis database number")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis password")
    REDIS_DEFAULT_TTL: int = Field(default=900, description="Redis default TTL in seconds (15 minutes)")

    class Config:
        """Pydantic configuration"""
        env_file = str(env_file_path)
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


class EmbeddingSettings(BaseSettings):
    """Embedding service settings"""
    EMBEDDING_PROVIDER: str = Field(default="onnx-service", description="Embedding provider (openai, triton, or onnx-service)")
    ONNX_SERVICE_URL: str = Field(default="http://localhost:7000", description="ONNX Service URL")
    EMBEDDING_DIMENSION: int = Field(default=768, description="Embedding dimension")
    EMBEDDING_MODEL: str = Field(default="paraphrase-multilingual-mpnet-base-v2", description="Embedding model")
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key")
    OPENAI_API_BASE: Optional[str] = Field(default=None, description="OpenAI API base")
    TRITON_URL: str = Field(default="http://localhost:8000", description="Triton URL")
    TRITON_MODEL_NAME: str = Field(default="paraphrase-multilingual-mpnet-base-v2", description="Triton model name")

    class Config:
        """Pydantic configuration"""
        env_file = str(env_file_path)
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


class LLMSettings(BaseSettings):
    """LLM service settings"""
    LITELLM_BASE_URL: str = Field(default="http://localhost:4000", description="LiteLLM base URL")
    LITELLM_API_KEY: str = Field(default="gach-llmops", description="LiteLLM API key")
    LITELLM_DB_HOST: str = Field(default="localhost", description="LiteLLM database host")
    LITELLM_DB_PORT: int = Field(default=5432, description="LiteLLM database port")
    LITELLM_DB_NAME: str = Field(default="litellm", description="LiteLLM database name")
    LITELLM_DB_USER: str = Field(default="gachai_db", description="LiteLLM database user")
    LITELLM_DB_PASSWORD: str = Field(default="gachai@123", description="LiteLLM database password")
    LITELLM_STORE_MODEL_IN_DB: bool = Field(default=True, description="Store model in database")
    LLM_MODEL: str = Field(default="groq", description="LLM model")
    LLM_TEMPERATURE: float = Field(default=0.7, description="LLM temperature")
    LLM_MAX_TOKENS: int = Field(default=4096, description="LLM max tokens")
    LLM_STREAMING: bool = Field(default=False, description="LLM streaming")
    LLM_TIMEOUT: int = Field(default=60, description="LLM timeout")
    SHOPPING_CART_API_URL: str = Field(default="https://gach.ai:7851/api/app/shopping-cart", description="Shopping cart API URL")
    SHOPPING_CART_API_TIMEOUT: int = Field(default=30, description="Shopping cart API timeout")
    TOP_K: int = Field(default=5, description="Default top K results for search")
    SIMILARITY_THRESHOLD: float = Field(default=0.7, description="Default similarity threshold for search")
    GROQ_API_KEY: str = Field(default="gach-llmops", description="Groq API key")

    @property
    def litellm_database_url(self) -> str:
        """Get LiteLLM database connection URL"""
        return f"postgresql://{self.LITELLM_DB_USER}:{self.LITELLM_DB_PASSWORD}@{self.LITELLM_DB_HOST}:{self.LITELLM_DB_PORT}/{self.LITELLM_DB_NAME}"

    class Config:
        """Pydantic configuration"""
        env_file = str(env_file_path)
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


class DatabaseSettings(BaseSettings):
    """PostgreSQL database settings"""
    POSTGRES_HOST: str = Field(default="localhost", description="PostgreSQL host")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")
    POSTGRES_DB: str = Field(default="gachai_db", description="PostgreSQL database name")
    POSTGRES_USER: str = Field(default="gachai_db", description="PostgreSQL user")
    POSTGRES_PASSWORD: str = Field(default="gachai@123", description="PostgreSQL password")
    POSTGRES_MIN_POOL_SIZE: int = Field(default=5, description="Minimum connection pool size")
    POSTGRES_MAX_POOL_SIZE: int = Field(default=20, description="Maximum connection pool size")
    ENABLE_DATABASE_LOGGING: bool = Field(default=True, description="Enable logging to database")
    DATABASE_LOG_RETENTION_DAYS: int = Field(default=30, description="Number of days to retain database logs")

    class Config:
        """Pydantic configuration"""
        env_file = str(env_file_path)
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


class GuardrailsSettings(BaseSettings):
    """Guardrails settings"""
    GUARDRAILS_CONFIG_PATH: str = Field(default="../../../guardrails", description="Guardrails configuration path (relative to SETTINGS_DIR or absolute)")
    ENABLE_INPUT_VALIDATION: bool = Field(default=True, description="Enable input validation")
    ENABLE_OUTPUT_VALIDATION: bool = Field(default=True, description="Enable output validation")
    ENABLE_PII_MASKING: bool = Field(default=True, description="Enable PII masking")
    GUARD_MODEL: str = Field(default="groq-llama-guard", description="Guardrails model")
    GUARD_BASE_URL: str = Field(default="http://localhost:4000", description="Guardrails base URL")
    GUARD_API_KEY: str = Field(default="gach-llmops", description="Guardrails API key")

    @property
    def CONFIG_PATH(self) -> str:
        """
        Get resolved guardrails config path
        Resolves relative paths from settings.py location, absolute paths are used as-is
        """
        config_path = Path(self.GUARDRAILS_CONFIG_PATH)

        # If path is absolute, use as-is
        if config_path.is_absolute():
            return str(config_path)

        # Resolve relative path from settings.py location
        # Path(__file__).parent = app/src/infrastructure/config/
        base_dir = Path(__file__).parent
        return str((base_dir / config_path).resolve())

    class Config:
        """Pydantic configuration"""
        env_file = str(env_file_path)
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


class LangfuseSettings(BaseSettings):
    """Langfuse observability settings"""
    LANGFUSE_PUBLIC_KEY: str = Field(default="", description="Langfuse public key")
    LANGFUSE_SECRET_KEY: str = Field(default="", description="Langfuse secret key")
    LANGFUSE_HOST: str = Field(default="https://cloud.langfuse.com", description="Langfuse host")
    LANGFUSE_ENVIRONMENT: str = Field(default="production", description="Langfuse environment")

    @property
    def ENVIRONMENT(self) -> str:
        """Backward compatibility: alias for LANGFUSE_ENVIRONMENT"""
        return self.LANGFUSE_ENVIRONMENT

    class Config:
        """Pydantic configuration"""
        env_file = str(env_file_path)
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


# Global settings instances
settings = Settings()
milvus_settings = MilvusSettings()
redis_settings = RedisSettings()
embedding_settings = EmbeddingSettings()
llm_settings = LLMSettings()
database_settings = DatabaseSettings()
guardrails_settings = GuardrailsSettings()
langfuse_settings = LangfuseSettings()

# Legacy: db_settings for backward compatibility
db_settings = database_settings
