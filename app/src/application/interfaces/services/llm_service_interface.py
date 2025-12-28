"""
LLM Service Interface
Abstract interface for LLM service
"""
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional


class ILLMService(ABC):
    """
    Interface for LLM service

    Domain layer interface - no infrastructure dependencies.
    Implementation details (LiteLLM, model names, etc.) are in infrastructure layer.
    """

    @abstractmethod
    async def invoke(self, prompt: str, **kwargs) -> str:
        """
        Generate response from LLM

        Args:
            prompt: Prompt text
            **kwargs: Additional parameters

        Returns:
            Generated response
        """
        pass

    @abstractmethod
    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        Stream response from LLM

        Args:
            prompt: Prompt text
            **kwargs: Additional parameters

        Yields:
            Response chunks
        """
        pass

