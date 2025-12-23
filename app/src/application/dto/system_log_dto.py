"""
System Log Data Transfer Objects
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class SystemLogLevel(str, Enum):
    """System log level enum"""
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"


class SystemLogCreateDTO(BaseModel):
    """DTO for creating a system log entry"""
    service_name: str = Field(..., description="Service name (chatbot, image-search, api)")
    level: SystemLogLevel = Field(..., description="Log level")
    message: str = Field(..., description="Log message", min_length=1)
    error_type: Optional[str] = Field(default=None, description="Error type/class name")
    stack_trace: Optional[str] = Field(default=None, description="Stack trace for errors")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata (JSONB)")

    class Config:
        json_schema_extra = {
            "example": {
                "service_name": "chatbot",
                "level": "ERROR",
                "message": "Failed to generate response from LLM",
                "error_type": "LLMAPIException",
                "stack_trace": "Traceback (most recent call last)...",
                "metadata": {
                    "session_id": "sess_123",
                    "user_id": "user_456",
                    "model": "groq"
                }
            }
        }


class SystemLogDTO(BaseModel):
    """System log entry DTO"""
    id: int = Field(..., description="Log ID")
    service_name: str = Field(..., description="Service name")
    level: SystemLogLevel = Field(..., description="Log level")
    message: str = Field(..., description="Log message")
    error_type: Optional[str] = Field(default=None, description="Error type")
    stack_trace: Optional[str] = Field(default=None, description="Stack trace")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadata")
    created_at: datetime = Field(..., description="Creation timestamp")


class SystemLogQueryDTO(BaseModel):
    """DTO for querying system logs"""
    service_name: Optional[str] = Field(default=None, description="Filter by service name")
    level: Optional[SystemLogLevel] = Field(default=None, description="Filter by log level")
    start_date: Optional[datetime] = Field(default=None, description="Start date filter")
    end_date: Optional[datetime] = Field(default=None, description="End date filter")
    search_text: Optional[str] = Field(default=None, description="Search in message")
    limit: int = Field(default=100, description="Maximum results", ge=1, le=1000)
    offset: int = Field(default=0, description="Offset for pagination", ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "service_name": "chatbot",
                "level": "ERROR",
                "start_date": "2025-12-20T00:00:00Z",
                "end_date": "2025-12-20T23:59:59Z",
                "limit": 100,
                "offset": 0
            }
        }


class SystemLogResponseDTO(BaseModel):
    """Response DTO for system logs query"""
    logs: List[SystemLogDTO] = Field(..., description="List of log entries")
    total_count: int = Field(..., description="Total number of logs matching query")
    page_size: int = Field(..., description="Number of logs in current page")
    offset: int = Field(..., description="Current offset")


class LogStatsDTO(BaseModel):
    """DTO for log statistics"""
    service_name: str = Field(..., description="Service name")
    total_logs: int = Field(..., description="Total number of logs")
    info_count: int = Field(default=0, description="INFO logs count")
    warn_count: int = Field(default=0, description="WARN logs count")
    error_count: int = Field(default=0, description="ERROR logs count")
    fatal_count: int = Field(default=0, description="FATAL logs count")
    last_error: Optional[datetime] = Field(default=None, description="Last error timestamp")
    last_fatal: Optional[datetime] = Field(default=None, description="Last fatal timestamp")

