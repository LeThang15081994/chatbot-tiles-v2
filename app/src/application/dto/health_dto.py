"""
Health Check-related Data Transfer Objects
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum


class HealthStatus(str, Enum):
    """Health status enum"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class ServiceHealthDTO(BaseModel):
    """Single service health DTO"""
    status: HealthStatus = Field(..., description="Service health status")
    type: str = Field(..., description="Service type (database, redis, milvus, llm, embedding)")
    response_time_ms: Optional[int] = Field(default=None, description="Response time in milliseconds")
    error: Optional[str] = Field(default=None, description="Error message if unhealthy")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional service details")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "type": "milvus",
                "response_time_ms": 45,
                "details": {
                    "version": "2.4.7",
                    "collections": ["company_document", "products"]
                }
            }
        }


class HealthCheckResponseDTO(BaseModel):
    """Health check response DTO"""
    status: HealthStatus = Field(..., description="Overall system health status")
    service_name: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    uptime_human: str = Field(..., description="Human-readable uptime")
    timestamp: str = Field(..., description="Health check timestamp")
    environment: str = Field(..., description="Environment (development, production)")
    services: List[ServiceHealthDTO] = Field(..., description="Individual service health status")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "service_name": "Ceramic Tiles Chatbot",
                "version": "1.0.0",
                "uptime_seconds": 3600.5,
                "uptime_human": "1h 0m 0s",
                "timestamp": "2025-12-20T10:30:00Z",
                "environment": "production",
                "services": [
                    {
                        "status": "healthy",
                        "type": "database",
                        "response_time_ms": 15
                    },
                    {
                        "status": "healthy",
                        "type": "redis",
                        "response_time_ms": 8
                    },
                    {
                        "status": "healthy",
                        "type": "milvus",
                        "response_time_ms": 45
                    }
                ]
            }
        }


class ReadinessCheckResponseDTO(BaseModel):
    """Readiness check response DTO"""
    ready: bool = Field(..., description="Service readiness status")
    message: str = Field(..., description="Readiness message")
    required_services: List[str] = Field(..., description="List of required services")
    ready_services: List[str] = Field(..., description="List of ready services")
    not_ready_services: List[str] = Field(..., description="List of not ready services")

