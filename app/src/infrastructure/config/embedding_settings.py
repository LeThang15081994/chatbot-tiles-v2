"""
Embedding Configuration Settings
"""
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class EmbeddingSettings(BaseSettings):
    """Embedding configuration"""

    # Embedding Provider (openai, triton, or onnx-service)
    EMBEDDING_PROVIDER: str = Field(default="onnx-service", description="Embedding provider")
    # ONNX Service Configuration (if provider=onnx-service)
    ONNX_SERVICE_URL: str = Field(default="http://localhost:7000", description="ONNX Service URL") # Recommended: lightweight alternative to Triton
    # Model Dimension
    EMBEDDING_DIMENSION: int = Field(default=768, description="Embedding dimension")

    # OpenAI Configuration (if provider=openai)
    EMBEDDING_MODEL: str = Field(default="paraphrase-multilingual-mpnet-base-v2", description="Embedding model")
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key")
    OPENAI_API_BASE: Optional[str] = Field(default=None, description="OpenAI API base")

    # Triton Configuration (if provider=triton)
    TRITON_URL: str = Field(default="http://localhost:8000", description="Triton URL")
    TRITON_MODEL_NAME: str = Field(default="paraphrase-multilingual-mpnet-base-v2", description="Triton model name")

    class Config:
        env_file = ".env"
        case_sensitive = True

