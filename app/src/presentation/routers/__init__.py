"""
Presentation Routers
Exports all router modules
"""
from .chat_router import router as chat_router
from .document_router import router as document_router
from .health_router import router as health_router

__all__ = [
    "chat_router",
    "document_router",
    "health_router",
]

