"""
Embedding Configuration Settings
"""
from typing import Optional
from pydantic_settings import BaseSettings


class EmbeddingSettings(BaseSettings):
    """Embedding configuration"""

    # Embedding Provider (openai, triton, or onnx-service)
    EMBEDDING_PROVIDER: str = "onnx-service"  # Recommended: lightweight alternative to Triton

    # OpenAI Configuration (if provider=openai)
    EMBEDDING_MODEL: str = "paraphrase-multilingual-mpnet-base-v2"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_BASE: Optional[str] = None

    # Triton Configuration (if provider=triton)
    TRITON_URL: str = "http://localhost:8000"
    TRITON_MODEL_NAME: str = "paraphrase-multilingual-mpnet-base-v2"

    # ONNX Service Configuration (if provider=onnx-service)
    ONNX_SERVICE_URL: str = "http://localhost:7000"

    # Model Dimension
    EMBEDDING_DIMENSION: int = 768  # paraphrase-multilingual-mpnet-base-v2 dimension

    class Config:
        env_file = ".env"
        case_sensitive = True

