"""
Embedding Model Entity
Represents an embedding model configuration in the RAG system
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from uuid import uuid4


class EmbeddingProvider(str, Enum):
    """Embedding provider enumeration"""
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    HUGGINGFACE = "huggingface"
    COHERE = "cohere"
    SENTENCE_TRANSFORMERS = "sentence_transformers"
    FASTEMBED = "fastembed"
    CUSTOM = "custom"


@dataclass
class EmbeddingModel:
    """
    Embedding model entity

    Represents an embedding model configuration.
    Stores model metadata, configuration, and performance metrics.
    """

    model_name: str
    provider: EmbeddingProvider
    model_id: str = field(default_factory=lambda: str(uuid4()))
    dimension: int = 1536  # Default for OpenAI
    max_input_length: int = 8191
    batch_size: int = 32
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    model_kwargs: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model information

        Returns:
            Dictionary with model info
        """
        return {
            "model_id": self.model_id,
            "model_name": self.model_name,
            "provider": self.provider.value,
            "dimension": self.dimension,
            "max_input_length": self.max_input_length,
            "batch_size": self.batch_size,
            "is_active": self.is_active
        }

    def is_openai_model(self) -> bool:
        """Check if this is an OpenAI model"""
        return self.provider in [EmbeddingProvider.OPENAI, EmbeddingProvider.AZURE_OPENAI]

    def is_local_model(self) -> bool:
        """Check if this is a local model"""
        return self.provider in [
            EmbeddingProvider.SENTENCE_TRANSFORMERS,
            EmbeddingProvider.FASTEMBED,
            EmbeddingProvider.HUGGINGFACE
        ]

    def requires_api_key(self) -> bool:
        """Check if model requires API key"""
        return self.provider in [
            EmbeddingProvider.OPENAI,
            EmbeddingProvider.AZURE_OPENAI,
            EmbeddingProvider.COHERE
        ]

    def validate_input_length(self, text_length: int) -> bool:
        """
        Validate input text length

        Args:
            text_length: Length of input text

        Returns:
            True if valid
        """
        return text_length <= self.max_input_length

    def calculate_optimal_batch_size(self, total_items: int) -> int:
        """
        Calculate optimal batch size for processing

        Args:
            total_items: Total number of items to process

        Returns:
            Optimal batch size
        """
        if total_items <= self.batch_size:
            return total_items

        # Ensure we process in even batches
        return min(self.batch_size, max(1, total_items // 10))

    def update_metadata(self, key: str, value: Any) -> None:
        """
        Update model metadata

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value

    def deactivate(self) -> None:
        """Deactivate model"""
        self.is_active = False

    def activate(self) -> None:
        """Activate model"""
        self.is_active = True

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary (safe - no secrets)

        Returns:
            Dictionary representation
        """
        return {
            "model_id": self.model_id,
            "model_name": self.model_name,
            "provider": self.provider.value,
            "dimension": self.dimension,
            "max_input_length": self.max_input_length,
            "batch_size": self.batch_size,
            "is_active": self.is_active,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }

    def __repr__(self) -> str:
        return (
            f"EmbeddingModel("
            f"name={self.model_name}, "
            f"provider={self.provider.value}, "
            f"dim={self.dimension}, "
            f"active={self.is_active}"
            f")"
        )

