"""
Chat Controller
Handles chat-related WebSocket requests (streaming and non-streaming)
"""
from typing import AsyncGenerator, Dict, Any, List
import uuid
import time
from datetime import datetime

from app.src.application.use_cases.rag_use_case import RAGUseCase
from app.src.application.dto.chat_dto import (
    ChatRequestDTO,
    WebSocketMessageDTO,
)
from app.src.infrastructure.config.settings import settings


class ChatController:
    """
    Chat Controller

    Orchestrates chat use cases and formats responses
    """

    def __init__(self, rag_use_case: RAGUseCase):
        """
        Initialize chat controller

        Args:
            rag_use_case: RAG use case for chat functionality
        """
        self.rag_use_case = rag_use_case

    async def chat_stream(
        self,
        message: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Handle WebSocket chat request (streaming)

        Args:
            message: WebSocket chat message (dict)

        Yields:
            WebSocket chat responses (dict)
        """
        start_time = time.time()

        try:
            # Generate session_id and user_id if not provided
            session_id = message.get("session_id") or f"session_{str(uuid.uuid4())[:8]}"
            user_id = message.get("user_id") or f"user_{str(uuid.uuid4())[:8]}"

            # Send START message
            yield {
                "type": "start",
                "message": "Processing your request...",
                "session_id": session_id,
                "user_id": user_id,
            }

            # Convert message to DTO
            chat_request_dto = ChatRequestDTO(
                question=message.get("query") or message.get("question", ""),
                session_id=session_id,
                user_id=user_id,
                stream=True,
            )

            # Execute streaming RAG use case
            sources_sent = False
            tokens_used = 0
            full_response = ""

            async for ws_message in self.rag_use_case.stream_chat(chat_request_dto):
                message_type = ws_message.type

                if message_type == "metadata" and not sources_sent:
                    # Metadata contains session info
                    pass

                elif message_type == "sources" and not sources_sent:
                    # Send sources if available
                    sources_data = ws_message.data if isinstance(ws_message.data, list) else []
                    sources = [
                        {
                            "id": doc.get("id", ""),
                            "title": doc.get("title", ""),
                            "source": doc.get("source", ""),
                            "score": doc.get("metadata", {}).get("score", 0.0),
                            "content_preview": doc.get("content", "")[:200] if doc.get("content") else None,
                        }
                        for doc in sources_data
                    ]

                    yield {
                        "type": "sources",
                        "sources": sources,
                    }
                    sources_sent = True

                elif message_type == "content":
                    # Send content chunk
                    content = ws_message.data if isinstance(ws_message.data, str) else str(ws_message.data)
                    full_response += content
                    tokens_used += len(content.split())  # Approximate

                    yield {
                        "type": "chunk",
                        "content": content,
                    }

                elif message_type == "products":
                    # Products metadata (optional)
                    pass

                elif message_type == "done":
                    # Send END message
                    latency_ms = (time.time() - start_time) * 1000

                    yield {
                        "type": "end",
                        "session_id": session_id,
                        "user_id": user_id,
                        "tokens_used": tokens_used,
                        "latency_ms": latency_ms,
                        "model": None,  # TODO: Add model tracking
                    }

        except Exception as e:
            # Send error message
            yield {
                "type": "error",
                "error": "ChatError",
                "message": str(e),
            }

    async def chat_non_stream(
        self,
        message: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Handle WebSocket chat request (non-streaming)
        Sends complete response in one message

        Args:
            message: WebSocket chat message (dict)

        Yields:
            WebSocket chat responses (dict)
        """
        start_time = time.time()

        try:
            # Generate session_id and user_id if not provided
            session_id = message.get("session_id") or f"session_{str(uuid.uuid4())[:8]}"
            user_id = message.get("user_id") or f"user_{str(uuid.uuid4())[:8]}"

            # Send START message
            yield {
                "type": "start",
                "message": "Processing your request...",
                "session_id": session_id,
                "user_id": user_id,
            }

            # Convert message to DTO
            chat_request_dto = ChatRequestDTO(
                question=message.get("query") or message.get("question", ""),
                session_id=session_id,
                user_id=user_id,
                stream=False,  # Force non-streaming
            )

            # Execute non-streaming RAG use case
            result = await self.rag_use_case.process_chat(chat_request_dto)

            # Send sources if available
            if result.sources:
                sources = [
                    {
                        "id": doc.get("id", ""),
                        "title": doc.get("title", ""),
                        "source": doc.get("source", ""),
                        "score": doc.get("metadata", {}).get("score", 0.0) if isinstance(doc.get("metadata"), dict) else 0.0,
                        "content_preview": doc.get("content", "")[:200] if doc.get("content") else None,
                    }
                    for doc in result.sources
                ]
                yield {
                    "type": "sources",
                    "sources": sources,
                }

            # Send complete response
            yield {
                "type": "response",
                "content": result.answer,
                "session_id": result.session_id,
                "user_id": result.user_id or user_id,
                "tokens_used": result.tokens_used,
                "latency_ms": result.latency_ms or result.processing_time_ms,
                "model": result.model,
                "products": result.products,
                "input_safe": result.input_safe,
                "output_safe": result.output_safe,
            }

            # Send END message
            latency_ms = (time.time() - start_time) * 1000
            yield {
                "type": "end",
                "session_id": result.session_id,
                "user_id": result.user_id or user_id,
                "tokens_used": result.tokens_used,
                "latency_ms": result.latency_ms or result.processing_time_ms or latency_ms,
                "model": result.model,
            }

        except Exception as e:
            # Send error message
            yield {
                "type": "error",
                "error": "ChatError",
                "message": str(e),
            }

    async def chat_websocket(
        self,
        message: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Unified WebSocket handler for both streaming and non-streaming modes

        Routes to appropriate handler based on 'stream' flag in message:
        - stream=True: Uses streaming mode (chat_stream)
        - stream=False: Uses non-streaming mode (chat_non_stream)

        Args:
            message: WebSocket chat message (dict) with 'stream' flag

        Yields:
            WebSocket chat responses (dict)
        """
        stream_mode = message.get("stream", True)  # Default to streaming for backward compatibility

        if stream_mode:
            # Use streaming mode
            async for chunk in self.chat_stream(message):
                yield chunk
        else:
            # Use non-streaming mode
            async for chunk in self.chat_non_stream(message):
                yield chunk

    async def get_conversation_history(
        self,
        user_id: str,
        session_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get conversation history

        Args:
            user_id: User ID (not used currently)
            session_id: Session ID

        Returns:
            List of conversation messages
        """
        history = await self.rag_use_case.get_chat_history(session_id)
        if history and hasattr(history, 'messages'):
            return [msg.model_dump() if hasattr(msg, 'model_dump') else msg.dict() for msg in history.messages]
        return []

    async def clear_conversation(
        self,
        user_id: str,
        session_id: str
    ) -> bool:
        """
        Clear conversation history

        Args:
            user_id: User ID (not used currently)
            session_id: Session ID

        Returns:
            True if successful
        """
        # TODO: Implement clear_history in RAGUseCase when needed
        # For now, return True as placeholder
        return True
