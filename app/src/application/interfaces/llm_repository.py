"""
LLM Repository Interface
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncGenerator, Optional
from app.src.application.dto.chat_dto import ChatMessageDTO


class ILLMRepository(ABC):
    """
    Interface for Large Language Model operations
    Abstracts the underlying LLM provider (OpenAI, Groq, etc.) via LiteLLM
    """

    @abstractmethod
    async def generate_response(
        self,
        messages: List[ChatMessageDTO],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> str:
        """
        Generate a response from LLM (non-streaming)

        Args:
            messages: List of chat messages
            model: Model name to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional model parameters

        Returns:
            Generated response text
        """
        pass

    @abstractmethod
    async def stream_response(
        self,
        messages: List[ChatMessageDTO],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response from LLM

        Args:
            messages: List of chat messages
            model: Model name to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional model parameters

        Yields:
            Response chunks
        """
        pass

    @abstractmethod
    async def generate_with_tools(
        self,
        messages: List[ChatMessageDTO],
        tools: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate response with tool/function calling

        Args:
            messages: List of chat messages
            tools: List of tool definitions
            model: Model name to use
            temperature: Sampling temperature
            **kwargs: Additional model parameters

        Returns:
            Response with tool calls if any
        """
        pass

    @abstractmethod
    async def stream_with_tools(
        self,
        messages: List[ChatMessageDTO],
        tools: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream response with tool/function calling

        Args:
            messages: List of chat messages
            tools: List of tool definitions
            model: Model name to use
            temperature: Sampling temperature
            **kwargs: Additional model parameters

        Yields:
            Response chunks with tool calls if any
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if LLM service is healthy and accessible

        Returns:
            True if healthy
        """
        pass

    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        Get list of available models

        Returns:
            List of model names
        """
        pass

