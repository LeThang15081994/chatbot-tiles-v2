"""
LiteLLM Client Implementation
Routes LLM requests through LiteLLM proxy with LangChain tool calling support
"""
import json
from typing import AsyncGenerator, List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.tools import StructuredTool
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from app.src.application.interfaces.llm_repository import ILLMRepository
from app.src.application.dto.chat_dto import ChatMessageDTO
from app.src.infrastructure.config.llm_settings import LLMSettings


class LiteLLMClient(ILLMRepository):
    """
    LiteLLM implementation of ILLMClient

    Routes all LLM requests through LiteLLM proxy for:
    - Load balancing
    - Cost tracking
    - Multiple provider support
    """

    def __init__(self, settings: LLMSettings):
        """
        Initialize LiteLLM client

        Args:
            settings: LLM configuration settings
        """
        self.settings = settings
        self.llm: Optional[ChatOpenAI] = None
        self.llm_with_tools: Optional[Any] = None
        self.tools: List[StructuredTool] = []
        self._initialize()

    def _initialize(self) -> None:
        """Initialize LangChain ChatOpenAI with LiteLLM proxy"""
        try:
            self.llm = ChatOpenAI(
                model=self.settings.LLM_MODEL,
                base_url=self.settings.LITELLM_BASE_URL,
                api_key=self.settings.LITELLM_API_KEY,
                temperature=self.settings.LLM_TEMPERATURE,
                max_tokens=self.settings.LLM_MAX_TOKENS,
                streaming=self.settings.LLM_STREAMING,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize LiteLLM client: {e}")

    def bind_tools(self, tools: List[StructuredTool]) -> None:
        """
        Bind tools to LLM for function calling

        Args:
            tools: List of LangChain StructuredTool instances
        """
        try:
            self.tools = tools
            self.llm_with_tools = self.llm.bind_tools(tools) if self.llm else None
        except Exception as e:
            raise RuntimeError(f"Failed to bind tools: {e}")

    def _convert_to_langchain_messages(self, messages: List[ChatMessageDTO]) -> List:
        """Convert ChatMessageDTO to LangChain messages"""
        langchain_messages = []
        for msg in messages:
            if msg.role == "system":
                langchain_messages.append(SystemMessage(content=msg.content))
            elif msg.role == "user":
                langchain_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                langchain_messages.append(AIMessage(content=msg.content))
            elif msg.role == "tool":
                # Tool message format
                tool_call_id = msg.metadata.get("tool_call_id") if msg.metadata else None
                langchain_messages.append(
                    ToolMessage(content=msg.content, tool_call_id=tool_call_id or "")
                )
        return langchain_messages

    def _extract_tool_calls(self, response: AIMessage) -> List[Dict[str, Any]]:
        """Extract tool calls from LLM response"""
        tool_calls = []
        if hasattr(response, 'tool_calls') and response.tool_calls:
            for tool_call in response.tool_calls:
                tool_calls.append({
                    "name": tool_call.get("name", ""),
                    "args": tool_call.get("args", {}),
                    "id": tool_call.get("id", "")
                })
        return tool_calls

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
        try:
            if not self.llm:
                raise RuntimeError("LLM not initialized")

            langchain_messages = self._convert_to_langchain_messages(messages)
            response = await self.llm.ainvoke(langchain_messages)
            return response.content if hasattr(response, 'content') else str(response)

        except Exception as e:
            raise RuntimeError(f"Generation failed: {e}")

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
        try:
            if not self.llm:
                raise RuntimeError("LLM not initialized")

            langchain_messages = self._convert_to_langchain_messages(messages)
            async for chunk in self.llm.astream(langchain_messages):
                if hasattr(chunk, 'content'):
                    yield chunk.content
                else:
                    yield str(chunk)

        except Exception as e:
            raise RuntimeError(f"Streaming generation failed: {e}")

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
            tools: List of tool definitions (not used, tools already bound)
            model: Model name to use
            temperature: Sampling temperature
            **kwargs: Additional model parameters

        Returns:
            Response with tool calls if any
        """
        try:
            if not self.llm_with_tools:
                raise RuntimeError("Tools not bound to LLM. Call bind_tools() first.")

            langchain_messages = self._convert_to_langchain_messages(messages)
            response: AIMessage = await self.llm_with_tools.ainvoke(langchain_messages)

            # Extract tool calls if any
            tool_calls = self._extract_tool_calls(response)

            return {
                "content": response.content if hasattr(response, 'content') else str(response),
                "tool_calls": tool_calls,
                "has_tool_calls": len(tool_calls) > 0
            }

        except Exception as e:
            raise RuntimeError(f"Tool generation failed: {e}")

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
            tools: List of tool definitions (not used, tools already bound)
            model: Model name to use
            temperature: Sampling temperature
            **kwargs: Additional model parameters

        Yields:
            Response chunks with tool calls if any
        """
        try:
            if not self.llm_with_tools:
                raise RuntimeError("Tools not bound to LLM. Call bind_tools() first.")

            langchain_messages = self._convert_to_langchain_messages(messages)
            full_content = ""
            tool_calls = []

            async for chunk in self.llm_with_tools.astream(langchain_messages):
                if hasattr(chunk, 'content'):
                    content = chunk.content
                    full_content += content
                    yield {
                        "type": "content",
                        "content": content
                    }
                elif hasattr(chunk, 'tool_calls') and chunk.tool_calls:
                    # Collect tool calls
                    for tool_call in chunk.tool_calls:
                        tool_calls.append({
                            "name": tool_call.get("name", ""),
                            "args": tool_call.get("args", {}),
                            "id": tool_call.get("id", "")
                        })
                    yield {
                        "type": "tool_calls",
                        "tool_calls": chunk.tool_calls
                    }

            # Final yield with complete response
            if tool_calls:
                yield {
                    "type": "final",
                    "content": full_content,
                    "tool_calls": tool_calls,
                    "has_tool_calls": True
                }
            else:
                yield {
                    "type": "final",
                    "content": full_content,
                    "tool_calls": [],
                    "has_tool_calls": False
                }

        except Exception as e:
            raise RuntimeError(f"Tool streaming failed: {e}")

    async def health_check(self) -> bool:
        """
        Check if LLM service is healthy and accessible

        Returns:
            True if healthy
        """
        try:
            if not self.llm:
                return False

            # Simple test generation
            response = await self.llm.ainvoke([HumanMessage(content="test")])
            return bool(response.content if hasattr(response, 'content') else str(response))

        except Exception:
            return False

    def get_available_models(self) -> List[str]:
        """
        Get list of available models

        Returns:
            List of model names
        """
        return [self.settings.LLM_MODEL] if self.settings.LLM_MODEL else []

