"""
LLM Configuration Value Object
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import Enum


class LLMProvider(str, Enum):
    """LLM provider enumeration"""
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LITELLM = "litellm"
    CUSTOM = "custom"


@dataclass(frozen=True)
class LLMConfig:
    """
    LLM configuration value object

    Represents configuration for LLM interactions.
    Immutable to ensure configuration consistency.
    """

    model_name: str
    provider: LLMProvider = LLMProvider.OPENAI
    temperature: float = 0.7
    max_tokens: int = 2000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    streaming: bool = True
    stop_sequences: Optional[tuple] = None
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    timeout: int = 60
    max_retries: int = 3
    additional_kwargs: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate LLM configuration"""
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("temperature must be between 0.0 and 2.0")

        if self.max_tokens < 1:
            raise ValueError("max_tokens must be positive")

        if not 0.0 <= self.top_p <= 1.0:
            raise ValueError("top_p must be between 0.0 and 1.0")

        if not -2.0 <= self.frequency_penalty <= 2.0:
            raise ValueError("frequency_penalty must be between -2.0 and 2.0")

        if not -2.0 <= self.presence_penalty <= 2.0:
            raise ValueError("presence_penalty must be between -2.0 and 2.0")

        if self.timeout < 1:
            raise ValueError("timeout must be positive")

        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")

        # Convert list to tuple if needed
        if isinstance(self.stop_sequences, list):
            object.__setattr__(self, 'stop_sequences', tuple(self.stop_sequences))

    @classmethod
    def default(cls, model_name: str = "gpt-4o-mini") -> 'LLMConfig':
        """
        Create default configuration

        Args:
            model_name: Model name

        Returns:
            Default LLMConfig
        """
        return cls(model_name=model_name)

    @classmethod
    def for_creative(cls, model_name: str = "gpt-4o") -> 'LLMConfig':
        """
        Create configuration for creative tasks

        Args:
            model_name: Model name

        Returns:
            Creative LLMConfig
        """
        return cls(
            model_name=model_name,
            temperature=1.0,
            top_p=0.95,
            max_tokens=3000
        )

    @classmethod
    def for_factual(cls, model_name: str = "gpt-4o-mini") -> 'LLMConfig':
        """
        Create configuration for factual tasks

        Args:
            model_name: Model name

        Returns:
            Factual LLMConfig
        """
        return cls(
            model_name=model_name,
            temperature=0.1,
            top_p=0.9,
            max_tokens=2000
        )

    @classmethod
    def for_chat(cls, model_name: str = "gpt-4o-mini") -> 'LLMConfig':
        """
        Create configuration for chat

        Args:
            model_name: Model name

        Returns:
            Chat LLMConfig
        """
        return cls(
            model_name=model_name,
            temperature=0.7,
            streaming=True,
            max_tokens=2000
        )

    @classmethod
    def for_summarization(cls, model_name: str = "gpt-4o-mini") -> 'LLMConfig':
        """
        Create configuration for summarization

        Args:
            model_name: Model name

        Returns:
            Summarization LLMConfig
        """
        return cls(
            model_name=model_name,
            temperature=0.3,
            max_tokens=1000
        )

    def is_streaming_enabled(self) -> bool:
        """Check if streaming is enabled"""
        return self.streaming

    def is_openai_model(self) -> bool:
        """Check if this is an OpenAI model"""
        return self.provider in [LLMProvider.OPENAI, LLMProvider.AZURE_OPENAI]

    def is_high_temperature(self) -> bool:
        """Check if temperature is high (>= 0.8)"""
        return self.temperature >= 0.8

    def is_low_temperature(self) -> bool:
        """Check if temperature is low (<= 0.3)"""
        return self.temperature <= 0.3

    def with_temperature(self, temperature: float) -> 'LLMConfig':
        """
        Create new config with different temperature

        Args:
            temperature: New temperature value

        Returns:
            New LLMConfig
        """
        return LLMConfig(
            model_name=self.model_name,
            provider=self.provider,
            temperature=temperature,
            max_tokens=self.max_tokens,
            top_p=self.top_p,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
            streaming=self.streaming,
            stop_sequences=self.stop_sequences,
            api_key=self.api_key,
            api_base=self.api_base,
            timeout=self.timeout,
            max_retries=self.max_retries,
            additional_kwargs=self.additional_kwargs
        )

    def with_streaming(self, streaming: bool) -> 'LLMConfig':
        """
        Create new config with streaming setting

        Args:
            streaming: Streaming enabled

        Returns:
            New LLMConfig
        """
        return LLMConfig(
            model_name=self.model_name,
            provider=self.provider,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=self.top_p,
            frequency_penalty=self.frequency_penalty,
            presence_penalty=self.presence_penalty,
            streaming=streaming,
            stop_sequences=self.stop_sequences,
            api_key=self.api_key,
            api_base=self.api_base,
            timeout=self.timeout,
            max_retries=self.max_retries,
            additional_kwargs=self.additional_kwargs
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary (safe - no secrets)

        Returns:
            Dictionary representation
        """
        return {
            "model_name": self.model_name,
            "provider": self.provider.value,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "streaming": self.streaming,
            "stop_sequences": list(self.stop_sequences) if self.stop_sequences else None,
            "timeout": self.timeout,
            "max_retries": self.max_retries
        }

    def __repr__(self) -> str:
        return (
            f"LLMConfig("
            f"model={self.model_name}, "
            f"temp={self.temperature}, "
            f"max_tokens={self.max_tokens}, "
            f"streaming={self.streaming}"
            f")"
        )

