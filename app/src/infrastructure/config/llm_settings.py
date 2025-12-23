"""
LLM Configuration Settings
"""
from pydantic_settings import BaseSettings
from typing import Optional


class LLMSettings(BaseSettings):
    """LLM configuration for LiteLLM"""

    # LiteLLM Router
    LITELLM_BASE_URL: str = "http://localhost:4000"
    LITELLM_API_KEY: str = "gach-llmops"

    # LiteLLM Router Database (for model management and cost tracking)
    # Uses shared PostgreSQL instance from db/postgresql
    LITELLM_DB_HOST: str = "postgres-db"
    LITELLM_DB_PORT: int = 5432
    LITELLM_DB_NAME: str = "litellm"
    LITELLM_DB_USER: str = "gachai_db"  # Same user as system logging
    LITELLM_DB_PASSWORD: str = "gachai@123"  # Same password as system logging
    LITELLM_STORE_MODEL_IN_DB: bool = True

    # Model Configuration
    LLM_MODEL: str = "groq"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 4096
    LLM_STREAMING: bool = True
    LLM_TIMEOUT: int = 60

    # Shopping Cart API Configuration
    SHOPPING_CART_API_URL: str = "https://gach.ai:7851/api/app/shopping-cart"
    SHOPPING_CART_API_TIMEOUT: int = 30  # seconds

    @property
    def litellm_database_url(self) -> str:
        """Get LiteLLM database connection URL"""
        return f"postgresql://{self.LITELLM_DB_USER}:{self.LITELLM_DB_PASSWORD}@{self.LITELLM_DB_HOST}:{self.LITELLM_DB_PORT}/{self.LITELLM_DB_NAME}"

    class Config:
        env_file = ".env"
        case_sensitive = True

