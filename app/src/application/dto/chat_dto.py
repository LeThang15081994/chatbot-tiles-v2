"""
Chat-related Data Transfer Objects
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatMessageDTO(BaseModel):
    """Single chat message DTO"""
    role: str = Field(..., description="Message role: user, assistant, system")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(default=None, description="Message timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class ChatRequestDTO(BaseModel):
    """Chat request DTO"""
    question: str = Field(..., description="User question", min_length=1, alias="query")
    session_id: Optional[str] = Field(default=None, description="Session ID for conversation history")
    user_id: Optional[str] = Field(default=None, description="User ID for tracking")
    conversation_id: Optional[str] = Field(default=None, description="Conversation identifier")
    stream: bool = Field(default=True, description="Enable streaming response")

    # Search configuration
    top_k: int = Field(default=5, ge=1, le=20, description="Number of documents to retrieve")
    similarity_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Similarity threshold")
    search_type: str = Field(default="hybrid", description="Search type: similarity, bm25, hybrid")

    # LLM configuration
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="LLM temperature")
    max_tokens: Optional[int] = Field(default=None, ge=1, le=4096, description="Max tokens to generate")

    # Filters and metadata
    metadata_filter: Optional[Dict[str, Any]] = Field(default=None, description="Metadata filters")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

    class Config:
        populate_by_name = True  # Allow both 'query' and 'question'
        json_schema_extra = {
            "example": {
                "question": "Gạch wooden là gì?",
                "session_id": "uuid-session-123",
                "user_id": "user_456",
                "stream": True
            }
        }


class ChatResponseDTO(BaseModel):
    """Chat response DTO"""
    answer: str = Field(..., description="Assistant answer")
    session_id: str = Field(..., description="Session ID")
    user_id: Optional[str] = Field(default=None, description="User ID")
    conversation_id: Optional[str] = Field(default=None, description="Conversation identifier")

    # Retrieved documents
    sources: Optional[List[Dict[str, Any]]] = Field(default=None, description="Source documents")
    products: Optional[List[Dict[str, Any]]] = Field(default=None, description="Related products")

    # Metadata
    tokens_used: Optional[int] = Field(default=None, description="Tokens used")
    latency_ms: Optional[float] = Field(default=None, description="Response latency in ms")
    model: Optional[str] = Field(default=None, description="Model used")

    # Guardrails
    input_safe: Optional[bool] = Field(default=True, description="Input passed guardrails validation")
    output_safe: Optional[bool] = Field(default=True, description="Output passed guardrails validation")

    # Additional metadata
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    processing_time_ms: Optional[int] = Field(default=None, description="Processing time in milliseconds")

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Gạch wooden là loại gạch...",
                "session_id": "uuid-session-123",
                "user_id": "user_456",
                "sources": [{"content": "...", "metadata": {}}],
                "products": [{"productCode": "WD001", "link": "..."}],
                "processing_time_ms": 1500
            }
        }


class WebSocketMetadataDTO(BaseModel):
    """WebSocket metadata DTO"""
    session_id: str = Field(..., description="Session ID")
    user_id: Optional[str] = Field(default=None, description="User ID")
    timestamp: Optional[datetime] = Field(default=None, description="Message timestamp")


class WebSocketMessageDTO(BaseModel):
    """WebSocket message DTO for streaming responses"""
    type: str = Field(..., description="Message type: content, metadata, products, done, error")
    data: Any = Field(..., description="Message data")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "type": "content",
                    "data": "Gạch wooden là...",
                    "metadata": {"chunk_index": 1}
                },
                {
                    "type": "products",
                    "data": [{"productCode": "WD001", "link": "..."}],
                    "metadata": {}
                },
                {
                    "type": "done",
                    "data": "[END]",
                    "metadata": {}
                }
            ]
        }


class ChatHistoryRequestDTO(BaseModel):
    """Request DTO for fetching chat history"""
    session_id: str = Field(..., description="Session ID to fetch history for")
    limit: int = Field(default=12, description="Number of messages to return", ge=1, le=100)


class ChatHistoryResponseDTO(BaseModel):
    """Response DTO for chat history"""
    session_id: str = Field(..., description="Session ID")
    messages: List[ChatMessageDTO] = Field(..., description="Chat messages")
    total_count: int = Field(..., description="Total number of messages")


class WSChatMessageDTO(BaseModel):
    """WebSocket chat message DTO from client"""
    type: str = Field(..., description="Message type: chat, ping")
    query: Optional[str] = Field(default=None, description="User question (for chat type)", alias="question")
    session_id: Optional[str] = Field(default=None, description="Session ID")
    user_id: Optional[str] = Field(default=None, description="User ID")
    conversation_id: Optional[str] = Field(default=None, description="Conversation identifier")

    # Search configuration
    top_k: Optional[int] = Field(default=5, ge=1, le=20, description="Number of documents to retrieve")
    similarity_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Similarity threshold")
    search_type: Optional[str] = Field(default="hybrid", description="Search type")

    # LLM configuration
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0, description="LLM temperature")
    max_tokens: Optional[int] = Field(default=None, ge=1, le=4096, description="Max tokens")

    # Filters
    metadata_filter: Optional[Dict[str, Any]] = Field(default=None, description="Metadata filters")

    class Config:
        populate_by_name = True  # Allow both 'query' and 'question'
        json_schema_extra = {
            "example": {
                "type": "chat",
                "query": "Gạch wooden là gì?",
                "session_id": "uuid-session-123",
                "user_id": "user_456"
            }
        }

