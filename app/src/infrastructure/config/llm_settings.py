"""
LLM Configuration Settings
"""
from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import Field


class LLMSettings(BaseSettings):
    """LLM configuration for LiteLLM"""

    # LiteLLM Router
    LITELLM_BASE_URL: str = Field(default="http://localhost:4000", description="LiteLLM base URL")
    LITELLM_API_KEY: str = Field(default="gach-llmops", description="LiteLLM API key")

    # LiteLLM Router Database (for model management and cost tracking)
    # Uses shared PostgreSQL instance from db/postgresql
    LITELLM_DB_HOST: str = Field(default="localhost", description="LiteLLM database host")
    LITELLM_DB_PORT: int = Field(default=5432, description="LiteLLM database port")
    LITELLM_DB_NAME: str = Field(default="litellm", description="LiteLLM database name")
    LITELLM_DB_USER: str = Field(default="gachai_db", description="LiteLLM database user")
    LITELLM_DB_PASSWORD: str = Field(default="gachai@123", description="LiteLLM database password")
    LITELLM_STORE_MODEL_IN_DB: bool = True

    # Model Configuration
    LLM_MODEL: str = Field(default="groq", description="LLM model")
    LLM_TEMPERATURE: float = Field(default=0.7, description="LLM temperature")
    LLM_MAX_TOKENS: int = Field(default=4096, description="LLM max tokens")
    LLM_STREAMING: bool = Field(default=False, description="LLM streaming")
    LLM_TIMEOUT: int = Field(default=60, description="LLM timeout")

    # Shopping Cart API Configuration
    SHOPPING_CART_API_URL: str = Field(default="https://gach.ai:7851/api/app/shopping-cart", description="Shopping cart API URL")
    SHOPPING_CART_API_TIMEOUT: int = Field(default=30, description="Shopping cart API timeout")

    @property
    def litellm_database_url(self) -> str:
        """Get LiteLLM database connection URL"""
        return f"postgresql://{self.LITELLM_DB_USER}:{self.LITELLM_DB_PASSWORD}@{self.LITELLM_DB_HOST}:{self.LITELLM_DB_PORT}/{self.LITELLM_DB_NAME}"

    class Config:
        env_file = ".env"
        case_sensitive = True

