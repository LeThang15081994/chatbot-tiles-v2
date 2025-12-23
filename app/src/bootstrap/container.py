"""
Dependency Injection Container
Uses dependency-injector for managing dependencies
"""
from dependency_injector import containers, providers

from app.src.infrastructure.config.settings import settings
from app.src.infrastructure.milvus import MilvusVectorStoreRepository
from app.src.infrastructure.redis import RedisCacheRepository
from app.src.infrastructure.llm import LiteLLMClient
from app.src.infrastructure.observability import LangfuseService
from app.src.infrastructure.guardrails import GuardrailsService
from app.src.infrastructure.embeddings import TritonEmbeddingService, ONNXServiceEmbedding
from app.src.infrastructure.postgresql import PostgreSQLDatabase
from app.src.infrastructure.logging.file_log_repository import FileLogRepository
from app.src.infrastructure.health import HealthRepository

from app.src.application.use_cases.rag_use_case import RAGUseCase
from app.src.application.use_cases.search_use_case import SearchUseCase
from app.src.application.use_cases.health_check_use_case import HealthCheckUseCase
from app.src.application.use_cases.system_log_use_case import SystemLogUseCase

from app.src.domain.services import (
    ContextBuilderService,
    PromptBuilderService
)

from app.src.presentation.controllers import (
    ChatController,
    DocumentController,
    HealthController,
)


class Container(containers.DeclarativeContainer):
    """
    Dependency Injection Container

    Manages all application dependencies with proper lifecycle
    """

    # Configuration
    config = providers.Singleton(lambda: settings)

    # Infrastructure - Core Services
    # Embedding service factory (ONNX Service, Triton, or OpenAI based on config)
    from app.src.infrastructure.embeddings import ONNXServiceEmbedding

    embedding_service = providers.Singleton(
        lambda settings: (
            ONNXServiceEmbedding(settings)
            if settings.EMBEDDING_PROVIDER == "onnx-service"
            else (
                TritonEmbeddingService(settings)
                if settings.EMBEDDING_PROVIDER == "triton"
                else ONNXServiceEmbedding(settings)  # Default to ONNX service
            )
        ),
        settings=config.provided.embedding
    )

    langfuse_service = providers.Singleton(
        LangfuseService,
        settings=config.provided.langfuse
    )

    guardrails_service = providers.Singleton(
        GuardrailsService,
        settings=config.provided.guardrails
    )

    # Infrastructure - Data Services
    milvus_repository = providers.Singleton(
        MilvusVectorStoreRepository,
        settings=config.provided.milvus,
        embedding_service=embedding_service
    )

    # Basic Redis cache (for non-semantic caching)
    redis_cache = providers.Singleton(
        RedisCacheRepository,
        settings=config.provided.redis
    )

    # Semantic cache (using LangChain RedisSemanticCache, similar to code cũ)
    from app.src.infrastructure.redis.semantic_cache import SemanticCacheRepository

    semantic_cache = providers.Singleton(
        SemanticCacheRepository,
        redis_settings=config.provided.redis,
        embedding_service=embedding_service,
        distance_threshold=0.2,  # Same as code cũ
        pre_cache_ttl=20,  # 20 seconds for pre-cache (before LLM call)
        post_cache_ttl=config.provided.redis.REDIS_DEFAULT_TTL  # 15 minutes for post-cache (after tool execution)
    )

    database = providers.Singleton(
        PostgreSQLDatabase,
        host=config.provided.database.POSTGRES_HOST,
        port=config.provided.database.POSTGRES_PORT,
        database=config.provided.database.POSTGRES_DB,
        user=config.provided.database.POSTGRES_USER,
        password=config.provided.database.POSTGRES_PASSWORD
    )

    # Infrastructure - System Logging
    # Use Factory instead of Singleton to delay initialization and handle errors gracefully
    def create_file_log_repository():
        """Factory function to create FileLogRepository with error handling"""
        try:
            return FileLogRepository()
        except Exception as e:
            print(f"Warning: Failed to create FileLogRepository: {e}")
            # Return a minimal implementation that does nothing but doesn't crash
            class DummyLogRepository:
                async def create_log(self, log): return 0
                async def get_logs(self, query): return type('obj', (object,), {'logs': [], 'total_count': 0, 'page_size': 0, 'offset': 0})()
                async def get_log_by_id(self, log_id): return None
                async def get_stats(self, service_name=None): return []
                async def delete_old_logs(self, days=15): return 0
                async def health_check(self): return False
            return DummyLogRepository()

    system_log_repository = providers.Singleton(
        create_file_log_repository
    )

    system_log_use_case = providers.Factory(
        SystemLogUseCase,
        log_repository=system_log_repository
    )

    # Infrastructure - LLM Client
    llm_client = providers.Singleton(
        LiteLLMClient,
        settings=config.provided.llm
    )

    # Presentation - LLM Tools (must be created before binding to LLM)
    from app.src.presentation.llm.search_tool import (
        create_company_info_tool,
        create_collection_info_tool,
        create_products_tool,
        create_add_to_cart_tool
    )

    # Domain Services
    context_builder = providers.Factory(
        ContextBuilderService,
        max_context_length=4000,
        include_metadata=True,
        include_scores=True
    )

    prompt_builder = providers.Factory(
        PromptBuilderService,
        include_context_header=True,
        include_history_header=True,
        langfuse_service=langfuse_service  # Inject LangfuseService to load prompts
    )

    # Domain - Summarization Service (giống code cũ)
    from app.src.domain.services.summarize_service import SummarizeService
    summarize_service = providers.Factory(
        SummarizeService,
        llm_service=llm_client,  # Use LLM for summarization (before tool binding)
        keep_last=4  # Keep last 4 messages, summarize older ones
    )

    # Application - Use Cases
    # SearchUseCase must be created before RAGUseCase and search_tool
    search_use_case = providers.Factory(
        SearchUseCase,
        vector_store=milvus_repository
    )

    # Application - Tools
    # Create company info tool
    company_info_tool = providers.Factory(
        create_company_info_tool,
        search_use_case=search_use_case
    )

    # Create collection info tool
    collection_info_tool = providers.Factory(
        create_collection_info_tool,
        search_use_case=search_use_case
    )

    # Create products tool
    products_tool = providers.Factory(
        create_products_tool,
        search_use_case=search_use_case
    )

    # Infrastructure - Shopping Cart Service
    from app.src.infrastructure.shopping_cart.shopping_cart_service import ShoppingCartService

    shopping_cart_service = providers.Singleton(
        ShoppingCartService,
        settings=config.provided.llm
    )

    # Create add to cart tool
    add_to_cart_tool = providers.Factory(
        create_add_to_cart_tool,
        search_use_case=search_use_case,
        shopping_cart_service=shopping_cart_service
    )

    # LLM Client with tools bound (wrapper factory)
    def create_llm_with_tools(
        llm=llm_client,
        company_tool=company_info_tool,
        collection_tool=collection_info_tool,
        products_tool=products_tool,
        cart_tool=add_to_cart_tool
    ):
        """Create LLM client and bind all four tools"""
        client = llm()
        company_tool_instance = company_tool()
        collection_tool_instance = collection_tool()
        products_tool_instance = products_tool()
        cart_tool_instance = cart_tool()
        # Bind all four tools to LLM
        client.bind_tools([
            company_tool_instance,
            collection_tool_instance,
            products_tool_instance,
            cart_tool_instance
        ])
        return client

    llm_client_with_tools = providers.Singleton(
        create_llm_with_tools,
        llm=llm_client,
        company_tool=company_info_tool,
        collection_tool=collection_info_tool,
        products_tool=products_tool,
        cart_tool=add_to_cart_tool
    )

    rag_use_case = providers.Factory(
        RAGUseCase,
        search_use_case=search_use_case,
        llm_service=llm_client_with_tools,
        cache_service=semantic_cache,
        guardrails_service=guardrails_service,
        langfuse_service=langfuse_service,
        context_builder=context_builder,
        prompt_builder=prompt_builder,
        summarize_service=summarize_service,  # Inject summarization service
        shopping_cart_service=shopping_cart_service  # Inject shopping cart service
    )

    health_repository = providers.Factory(
        HealthRepository,
        vector_store=milvus_repository,
        cache=redis_cache,
        llm_client=llm_client,
        database=database,
        embedding_service=embedding_service
    )

    health_check_use_case = providers.Factory(
        HealthCheckUseCase,
        health_repository=health_repository,
        service_name="Ceramic Tiles Chatbot",
        version="2.0.0"
    )

    # Presentation Layer - Controllers
    chat_controller = providers.Factory(
        ChatController,
        rag_use_case=rag_use_case  # RAGUseCase handles chat functionality
    )

    document_controller = providers.Factory(
        DocumentController,
        document_use_case=search_use_case,  # SearchUseCase handles document operations
        search_use_case=search_use_case  # Inject SearchUseCase for search operations
    )

    health_controller = providers.Factory(
        HealthController,
        health_check_use_case=health_check_use_case,  # Use HealthCheckUseCase
    )

