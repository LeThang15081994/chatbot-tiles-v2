"""
Main Entry Point and FastAPI Application Factory
Chatbot Tiles v2.0 - RAG System with Clean Architecture
"""
import uvicorn
import time
import logging
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager

from app.src.infrastructure.config.settings import (
    settings,
    database_settings,
    milvus_settings,
    redis_settings,
    llm_settings,
    embedding_settings
)
from app.src.infrastructure.logging.logger_repository import setup_app_logging

from app.src.presentation.routers.chat_router import router as chat_router
from app.src.presentation.routers.document_router import router as document_router
from app.src.presentation.routers.health_router import router as health_router

from .container import Container

# Setup logging first (before any other imports that might log)
setup_app_logging()
logger = logging.getLogger(__name__)


async def _check_startup_connections(container: Container):
    """
    Check connections to all services and databases during startup

    Args:
        container: Dependency injection container
    """
    from app.src.application.dto.health_dto import HealthStatus

    # Get health repository
    health_repo = container.health_repository()

    # Check PostgreSQL
    postgres_host = f"{database_settings.POSTGRES_HOST}:{database_settings.POSTGRES_PORT}"
    logger.info(f"Checking PostgreSQL connection: {postgres_host}")
    try:
        db_health = await health_repo.check_database_health()
        if db_health.status == HealthStatus.HEALTHY:
            logger.info(f"PostgreSQL connection successful: {postgres_host} (response time: {db_health.response_time_ms}ms)")
        else:
            logger.error(f"PostgreSQL connection failed: {postgres_host} - {db_health.error}")
    except Exception as e:
        logger.error(f"PostgreSQL connection error: {postgres_host} - {e}")

    # Check Milvus
    milvus_host = f"{milvus_settings.MILVUS_HOST}:{milvus_settings.MILVUS_PORT}"
    logger.info(f"Checking Milvus connection: {milvus_host}")
    try:
        milvus_health = await health_repo.check_milvus_health()
        if milvus_health.status == HealthStatus.HEALTHY:
            logger.info(f"Milvus connection successful: {milvus_host} (response time: {milvus_health.response_time_ms}ms)")
        else:
            logger.error(f"Milvus connection failed: {milvus_host} - {milvus_health.error}")
    except Exception as e:
        logger.error(f"Milvus connection error: {milvus_host} - {e}")

    # Check Redis
    redis_host = f"{redis_settings.REDIS_HOST}:{redis_settings.REDIS_PORT}"
    logger.info(f"Checking Redis connection: {redis_host}")
    try:
        redis_health = await health_repo.check_redis_health()
        if redis_health.status == HealthStatus.HEALTHY:
            logger.info(f"Redis connection successful: {redis_host} (response time: {redis_health.response_time_ms}ms)")
        else:
            logger.error(f"Redis connection failed: {redis_host} - {redis_health.error}")
    except Exception as e:
        logger.error(f"Redis connection error: {redis_host} - {e}")

    # Check LiteLLM
    litellm_url = llm_settings.LITELLM_BASE_URL
    logger.info(f"Checking LiteLLM connection: {litellm_url}")
    try:
        llm_health = await health_repo.check_llm_health()
        if llm_health.status == HealthStatus.HEALTHY:
            logger.info(f"✓ LiteLLM connection successful: {litellm_url} (response time: {llm_health.response_time_ms}ms)")
        else:
            logger.error(f"✗ LiteLLM connection failed: {litellm_url} - {llm_health.error}")
    except Exception as e:
        logger.error(f"✗ LiteLLM connection error: {litellm_url} - {e}")

    # Check ONNX Service
    onnx_url = embedding_settings.ONNX_SERVICE_URL
    logger.info(f"Checking ONNX Service connection: {onnx_url}")
    try:
        onnx_health = await health_repo.check_onnx_health()
        if onnx_health.status == HealthStatus.HEALTHY:
            logger.info(f"✓ ONNX Service connection successful: {onnx_url} (response time: {onnx_health.response_time_ms}ms)")
        else:
            logger.error(f"✗ ONNX Service connection failed: {onnx_url} - {onnx_health.error}")
    except Exception as e:
        logger.error(f"✗ ONNX Service connection error: {onnx_url} - {e}")

    logger.info("Startup connection checks completed.")


def setup_cors(app: FastAPI, allowed_origins: list = None):
    """
    Setup CORS middleware

    Args:
        app: FastAPI application
        allowed_origins: List of allowed origins (default: from settings or all)
    """
    if allowed_origins is None:
        # Use settings if available, otherwise allow all in dev
        if hasattr(settings, 'ALLOWED_ORIGINS') and settings.ALLOWED_ORIGINS:
            allowed_origins = settings.ALLOWED_ORIGINS
        else:
            allowed_origins = ["*"] if settings.APP_ENVIRONMENT == "development" else []

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
        logger.info(
            f"{method} {url}",
            extra={
                "method": method,
                "url": str(url),
                "client_ip": client_ip,
                "request_type": "http"
            }
        )

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Log response
        status_code = response.status_code
        log_level = logging.ERROR if status_code >= 500 else logging.WARNING if status_code >= 400 else logging.INFO
        logger.log(
            log_level,
            f"{method} {url} - Status: {status_code}",
            extra={
                "method": method,
                "url": str(url),
                "status_code": status_code,
                "duration_ms": duration_ms,
                "client_ip": client_ip
            }
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
    logger.info("Starting Chatbot Tiles v2.0...")

    # Initialize DI Container
    try:
        container = Container()
        container.wire(modules=[
            "app.src.presentation.routers.chat_router",
            "app.src.presentation.routers.document_router",
            "app.src.presentation.routers.health_router",
        ])

        app.state.container = container

        # Eager load prompts during startup
        # This ensures all prompts are loaded from Langfuse before accepting requests
        # Fail fast if prompts cannot be loaded
        logger.info("Loading prompts from Langfuse...")
        try:
            prompt_builder = container.prompt_builder()
            logger.info("All prompts loaded successfully from Langfuse")
        except Exception as e:
            logger.critical(
                f"Failed to load prompts from Langfuse: {e}",
                exc_info=True,
                extra={"error_type": type(e).__name__}
            )
            # Fail fast - do not start application if prompts cannot be loaded
            raise RuntimeError(
                "Application startup failed: Cannot load prompts from Langfuse. "
                "Please ensure all required prompts exist in Langfuse Dashboard with the correct label."
            ) from e

        # Load guardrails config during startup
        # This ensures config is loaded once and reused for all requests
        logger.info("Loading guardrails config...")
        try:
            # Initialize guardrails service (will load and cache config)
            guardrails_service = container.guardrails_service()
            if guardrails_service.rails is None:
                logger.warning("Guardrails config not found or disabled. Guardrails will not be available.")
            else:
                logger.info("Guardrails config loaded successfully.")
        except Exception as e:
            logger.warning(
                f"Failed to load guardrails config: {e}. Guardrails will be disabled.",
                exc_info=True,
                extra={"error_type": type(e).__name__}
            )
            # Don't fail startup if guardrails config fails - just disable guardrails
            # This allows the application to run without guardrails if needed

        # Check connections to all services and databases
        logger.info("Checking connections to services and databases...")
        await _check_startup_connections(container)

        logger.info("Application started successfully!")
    except Exception as e:
        logger.critical(
            "Failed to initialize application",
            exc_info=True,
            extra={"error_type": type(e).__name__}
        )
        raise

    yield

    # Shutdown
    logger.info("Shutting down Chatbot Tiles v2.0...")

    # Cleanup resources (if needed in future)
    logger.info("Application shutdown complete!")


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
    setup_cors(app)

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

