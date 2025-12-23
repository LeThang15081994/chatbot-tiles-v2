"""
Main Entry Point and FastAPI Application Factory
Chatbot Tiles v2.0 - RAG System with Clean Architecture
"""
import uvicorn
import time
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager

from app.src.infrastructure.config.settings import settings
from app.src.presentation.routers import (
    chat_router,
    document_router,
    health_router,
)
from .container import Container


def setup_cors(app: FastAPI, allowed_origins: list = None):
    """
    Setup CORS middleware

    Args:
        app: FastAPI application
        allowed_origins: List of allowed origins (default: all)
    """
    if allowed_origins is None:
        allowed_origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time"],
    )


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Request/Response logging middleware
    """

    async def dispatch(self, request: Request, call_next):
        """
        Log requests and responses

        Args:
            request: FastAPI request
            call_next: Next middleware

        Returns:
            Response with logging
        """
        # Start time
        start_time = time.time()

        # Request info
        method = request.method
        url = str(request.url)
        client_ip = request.client.host if request.client else "unknown"

        # Log request
        print(f"[{datetime.now().isoformat()}] {method} {url} - Client: {client_ip}")

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Log response
        status_code = response.status_code
        print(
            f"[{datetime.now().isoformat()}] {method} {url} - "
            f"Status: {status_code} - Duration: {duration_ms:.2f}ms"
        )

        # Add custom headers
        response.headers["X-Process-Time"] = f"{duration_ms:.2f}ms"
        if hasattr(request.state, "request_id"):
            response.headers["X-Request-ID"] = request.state.request_id

        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager

    Handles startup and shutdown events
    """
    # Startup
    print("Starting Chatbot Tiles v2.0...")

    # Initialize DI Container
    try:
        container = Container()
        container.wire(modules=[
            "src.presentation.routers.chat_router",
            "src.presentation.routers.document_router",
            "src.presentation.routers.health_router",
        ])

        app.state.container = container
        print("Application started successfully!")
    except Exception as e:
        print(f"ERROR: Failed to initialize application: {e}")
        import traceback
        traceback.print_exc()
        raise

    yield

    # Shutdown
    print("Shutting down Chatbot Tiles v2.0...")

    # Cleanup resources
    # await container.shutdown_resources()

    print("Application shutdown complete!")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application

    Returns:
        Configured FastAPI application
    """
    # Create FastAPI app
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="RAG-based Chatbot with Clean Architecture",
        docs_url=f"{settings.API_V1_STR}/docs",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan,
    )

    # Setup CORS
    setup_cors(app, allowed_origins=["*"])

    # Add middleware (order matters - last added runs first)
    app.add_middleware(LoggingMiddleware)

    # Register routers
    app.include_router(health_router)
    app.include_router(chat_router)
    app.include_router(document_router)

    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint"""
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "description": "RAG-based Chatbot with Clean Architecture",
            "docs": f"{settings.API_V1_STR}/docs",
            "health": f"{settings.API_V1_STR}/health",
        }

    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "app.src.bootstrap.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )

