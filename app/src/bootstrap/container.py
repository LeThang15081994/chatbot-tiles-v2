"""
Dependency Injection Container
Uses dependency-injector for managing dependencies
"""
import logging
from typing import Dict, Any
from dependency_injector import containers, providers

from app.src.infrastructure.config.settings import (
    settings,
    langfuse_settings,
    milvus_settings,
    redis_settings,
    embedding_settings,
    llm_settings,
    database_settings,
    guardrails_settings
)
from app.src.infrastructure.vectordb.milvus_repository import MilvusVectorStoreRepository
from app.src.infrastructure.proxy.litellm_client import LiteLLMClient
from app.src.infrastructure.observability.langfuse_service import LangfuseService
from app.src.infrastructure.guardrails.guardrails_service import GuardrailsService
# Embeddings imports will be done inside the container class where needed
from app.src.infrastructure.postgresql.database import PostgreSQLDatabase
from app.src.infrastructure.health.health_repository import HealthRepository

from app.src.application.use_cases.rag_use_case import RAGUseCase
from app.src.application.use_cases.search_use_case import SearchUseCase
from app.src.application.use_cases.health_check_use_case import HealthCheckUseCase

from app.src.domain.services.context_builder import ContextBuilderService
from app.src.domain.services.prompt_builder import PromptBuilderService
from app.src.domain.services.answer_cache_facade import AnswerCacheFacade

from app.src.presentation.controllers.chat_controller import ChatController
from app.src.presentation.controllers.document_controller import DocumentController
from app.src.presentation.controllers.health_controller import HealthController

from app.src.infrastructure.embeddings.onnx_embeddings import ONNXEmbeddings

from app.src.infrastructure.vectordb.langchain_retriever_factory import LangChainRetrieverFactory
from app.src.infrastructure.cache.context_cache import ContextCache
from app.src.infrastructure.cache.cached_retriever import CachedRetriever



class Container(containers.DeclarativeContainer):
    """
    Dependency Injection Container

    Manages all application dependencies with proper lifecycle
    """

    # Infrastructure - Core Services
    # Embedding service factory (ONNX Service, Triton, or OpenAI based on config)


    embedding_service = providers.Singleton(
        lambda settings: (
            ONNXEmbeddings(settings)
            if settings.EMBEDDING_PROVIDER == "onnx-service"
            else (
                ONNXEmbeddings(settings)
                if settings.EMBEDDING_PROVIDER == "onnx-service"
                else ONNXEmbeddings(settings)  # Default to ONNX service
            )
        ),
        settings=providers.Object(embedding_settings)
    )

    langfuse_service = providers.Singleton(
        LangfuseService,
        langfuse_settings=providers.Object(langfuse_settings)
    )

    guardrails_service = providers.Singleton(
        GuardrailsService,
        settings=providers.Object(guardrails_settings)
    )

    # Infrastructure - Data Services
    milvus_repository = providers.Singleton(
        MilvusVectorStoreRepository,
        settings=providers.Object(milvus_settings),
        embedding_service=embedding_service
    )

    # Semantic cache (using LangChain RedisSemanticCache, similar to code cũ)
    from app.src.infrastructure.cache.redis_semantic_cache import RedisSemanticCache

    semantic_cache = providers.Singleton(
        RedisSemanticCache,
        redis_settings=providers.Object(redis_settings),
        embedding_service=embedding_service,
        distance_threshold=0.2,  # Same as code cũ
        pre_cache_ttl=20,  # 20 seconds for pre-cache (before LLM call)
        post_cache_ttl=redis_settings.REDIS_DEFAULT_TTL  # 15 minutes for post-cache (after tool execution)
    )

    database = providers.Singleton(
        PostgreSQLDatabase,
        host=database_settings.POSTGRES_HOST,
        port=database_settings.POSTGRES_PORT,
        database=database_settings.POSTGRES_DB,
        user=database_settings.POSTGRES_USER,
        password=database_settings.POSTGRES_PASSWORD
    )

    # Infrastructure - LLM Client
    llm_client = providers.Singleton(
        LiteLLMClient,
        settings=providers.Object(llm_settings)
    )

    # Infrastructure - New 4-Layer Cache Components
    from app.src.infrastructure.cache.cached_embeddings import CachedONNXEmbeddings
    from app.src.infrastructure.embeddings.onnx_embeddings import ONNXEmbeddings
    from app.src.infrastructure.embeddings.embedding_service_wrapper import EmbeddingServiceWrapper
    from app.src.infrastructure.cache.redis_text_cache import RedisTextCache
    from app.src.infrastructure.cache.redis_vector_cache import RedisVectorCache
    from app.src.infrastructure.cache.redis_semantic_cache import RedisSemanticCache

    # Base embeddings (ONNX)
    base_embeddings = providers.Singleton(
        ONNXEmbeddings,
        settings=providers.Object(embedding_settings)
    )

    # Cached embeddings (Cache #2)
    cached_embeddings = providers.Singleton(
        CachedONNXEmbeddings,
        base_embeddings=base_embeddings,
        redis_settings=providers.Object(redis_settings),
        embedding_settings=providers.Object(embedding_settings),
        cache_ttl=600
    )

    # Embedding service wrapper (implements IEmbeddingService)
    embedding_service_wrapper = providers.Singleton(
        EmbeddingServiceWrapper,
        cached_embeddings=cached_embeddings
    )

    # Cache #1: Text cache
    text_cache = providers.Singleton(
        RedisTextCache,
        redis_settings=providers.Object(redis_settings),
        default_ttl=900
    )

    # Cache #3: Vector cache
    vector_cache = providers.Singleton(
        RedisVectorCache,
        redis_settings=providers.Object(redis_settings),
        default_ttl=900
    )

    # Cache #4: Semantic cache
    semantic_cache_new = providers.Singleton(
        RedisSemanticCache,
        redis_settings=providers.Object(redis_settings),
        dimension=embedding_settings.EMBEDDING_DIMENSION,
        similarity_threshold=0.8
    )


    # Context cache for retriever results
    context_cache = providers.Singleton(
        ContextCache,
        redis_settings=providers.Object(redis_settings),
        embedding_settings=providers.Object(embedding_settings),
        cache_ttl=600  # 15 minutes
    )

    # LangChain Retriever for AnswerCacheFacade (default: company_document_info)
    # Create base retriever first
    langchain_retriever_base = providers.Factory(
        lambda repo: LangChainRetrieverFactory.create_retriever(
            milvus_repository=repo,
            collection_name="company_document_info",
            k=5
        ),
        repo=milvus_repository
    )

    # Wrap with CachedRetriever
    langchain_retriever_cached = providers.Singleton(
        CachedRetriever,
        retriever=langchain_retriever_base,
        context_cache=context_cache,
        k=5,
        collection="company_document_info"
    )

    # Answer Cache Facade (4-layer caching orchestrator)
    # Uses llm_client (LiteLLMClient) which implements ILLMService
    # Uses LangChain Retriever (will be detected and used with query text)
    answer_cache_facade = providers.Singleton(
        AnswerCacheFacade,
        text_cache=text_cache,
        embedding_service=embedding_service_wrapper,
        vector_cache=vector_cache,
        semantic_cache=semantic_cache_new,
        retriever=langchain_retriever_cached,  # LangChain Retriever with Context Cache
        llm_service=llm_client,  # Use llm_client (implements ILLMService)
        guardrails_service=guardrails_service,
        similarity_threshold=0.8
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

    # Prompt Builder Service - Singleton to load prompts only once at bootstrap
    # All prompts are loaded from Langfuse during initialization and reused for all requests
    prompt_builder = providers.Singleton(
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
    # SearchUseCase now uses LangChain Retriever
    from app.src.infrastructure.vectordb.langchain_retriever_factory import LangChainRetrieverFactory

    # Create retriever factory wrapper (implements IRetrieverFactory)
    # This wrapper adapts LangChainRetrieverFactory static methods to instance methods
    class RetrieverFactoryWrapper:
        """Wrapper for LangChainRetrieverFactory to implement IRetrieverFactory interface"""
        def create_retriever(self, vector_store_repository, collection_name=None, k=5, filter_expr=None):
            return LangChainRetrieverFactory.create_retriever(
                milvus_repository=vector_store_repository,
                collection_name=collection_name,
                k=k,
                filter_expr=filter_expr
            )

        def create_retrievers_for_all_collections(self, vector_store_repository, k=5):
            return LangChainRetrieverFactory.create_retrievers_for_all_collections(
                milvus_repository=vector_store_repository,
                k=k
            )

    retriever_factory = providers.Singleton(RetrieverFactoryWrapper)

    search_use_case = providers.Factory(
        SearchUseCase,
        vector_store_repository=milvus_repository,  # MilvusVectorStoreRepository implements IVectorStoreRepository
        retriever_factory=retriever_factory,  # RetrieverFactoryWrapper implements IRetrieverFactory
        retrievers=None  # Will create retrievers on-demand
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
    from app.src.infrastructure.tool.shopping_cart_service import ShoppingCartService

    shopping_cart_service = providers.Singleton(
        ShoppingCartService,
        settings=providers.Object(llm_settings)
    )

    # Create add to cart tool
    add_to_cart_tool = providers.Factory(
        create_add_to_cart_tool,
        search_use_case=search_use_case,
        shopping_cart_service=shopping_cart_service
    )

    # Create structured_tools dict (LangChain StructuredTool instances)
    # This dict is used by LangGraph nodes for tool execution
    def create_structured_tools_dict(
        company_tool=company_info_tool,
        collection_tool=collection_info_tool,
        products_tool=products_tool,
        cart_tool=add_to_cart_tool
    ) -> Dict[str, Any]:
        """
        Create dict of LangChain StructuredTool instances

        Returns:
            Dict mapping tool names to StructuredTool instances
        """
        from langchain_core.tools import StructuredTool

        # Tools are already StructuredTool instances when injected (resolved from Factory providers)
        return {
            "search_company_info": company_tool,
            "search_collection_info": collection_tool,
            "search_products": products_tool,
            "add_to_cart": cart_tool
        }

    structured_tools_dict = providers.Singleton(
        create_structured_tools_dict,
        company_tool=company_info_tool,
        collection_tool=collection_info_tool,
        products_tool=products_tool,
        cart_tool=add_to_cart_tool
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
        client = llm
        # Tools are already resolved instances when injected
        client.bind_tools([
            company_tool,
            collection_tool,
            products_tool,
            cart_tool
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
        answer_cache_facade=answer_cache_facade,
        llm_raise=guardrails_service,  # GuardrailsService implements IGuardrailsService
        tracing_service=langfuse_service,  # LangfuseService implements ITracingService
        context_builder=context_builder,
        prompt_builder=prompt_builder,
        summarize_service=summarize_service,
        shopping_cart_service=shopping_cart_service,
        structured_tools=structured_tools_dict  # LangChain StructuredTool dict for LangGraph
    )

    health_repository = providers.Factory(
        HealthRepository,
        vector_store=milvus_repository,
        context_cache=context_cache,  # Use context_cache for Redis health check
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

