# Cấu Trúc Dự Án - Cây Thư Mục Chi Tiết

```
chatbot-tiles-v2/
│
├── app/
│   ├── guardrails/                    # Guardrails config
│   │   ├── config.yml
│   │   └── prompts.yml
│   │
│   ├── litellm/                       # LiteLLM router config
│   │   └── litellm_router_config.yaml
│   │
│   ├── logging/                       # Logging directory
│   │
│   └── src/
│       │
│       ├── bootstrap/                 # 🚀 Application Startup
│       │   ├── container.py          # DI Container (dependency-injector)
│       │   └── main.py               # FastAPI app entry point
│       │
│       ├── domain/                    # 🏛️ Domain Layer (Business Logic)
│       │   │
│       │   ├── entities/             # Domain Entities
│       │   │   ├── chat_session.py
│       │   │   ├── conversation_history.py
│       │   │   ├── document.py
│       │   │   ├── embedding_model.py
│       │   │   ├── message.py
│       │   │   ├── retrieval_result.py
│       │   │   └── tool_call.py
│       │   │
│       │   ├── interfaces/            # ✨ NEW: Domain Interfaces (4-layer caching)
│       │   │   ├── __init__.py
│       │   │   ├── text_cache_interface.py        # ITextCache
│       │   │   ├── embedding_service_interface.py  # IEmbeddingService
│       │   │   ├── vector_cache_interface.py       # IVectorCache
│       │   │   ├── semantic_cache_interface.py     # ISemanticCache
│       │   │   ├── retriever_interface.py          # IRetriever
│       │   │   └── llm_service_interface.py         # ILLMService
│       │   │
│       │   ├── services/              # Domain Services
│       │   │   ├── answer_cache_facade.py    # ✨ NEW: 4-layer cache orchestrator
│       │   │   ├── context_builder.py
│       │   │   ├── conversation_manager.py
│       │   │   ├── prompt_builder.py
│       │   │   ├── retrieval_optimizer.py
│       │   │   └── summarize_service.py
│       │   │
│       │   └── value_objects/         # Value Objects
│       │       ├── context.py
│       │       ├── llm_config.py
│       │       ├── prompt.py
│       │       ├── query.py
│       │       ├── retrieval_config.py
│       │       ├── search_filter.py
│       │       ├── session_id.py
│       │       └── user_id.py
│       │
│       ├── application/               # 📋 Application Layer (Use Cases)
│       │   │
│       │   ├── dto/                   # Data Transfer Objects
│       │   │   ├── chat_dto.py
│       │   │   ├── document_dto.py
│       │   │   ├── health_dto.py
│       │   │   ├── search_dto.py
│       │   │   └── system_log_dto.py
│       │   │
│       │   ├── interfaces/            # Application Interfaces (Legacy)
│       │   │   ├── cache_repository.py
│       │   │   ├── embedding_repository.py
│       │   │   ├── health_repository.py
│       │   │   ├── llm_repository.py
│       │   │   ├── system_log_repository.py
│       │   │   └── vector_store_repository.py
│       │   │
│       │   └── use_cases/             # Use Cases
│       │       ├── chat_service.py          # ✨ NEW: Chat với 4-layer caching
│       │       ├── health_check_use_case.py
│       │       ├── rag_use_case.py          # Legacy: RAG với tool calling
│       │       ├── search_use_case.py
│       │       └── system_log_use_case.py
│       │
│       ├── infrastructure/           # 🔧 Infrastructure Layer (Implementations)
│       │   │
│       │   ├── config/                 # Configuration
│       │   │   ├── database_settings.py
│       │   │   ├── embedding_settings.py
│       │   │   ├── env.example
│       │   │   ├── guardrails_settings.py
│       │   │   ├── langfuse_settings.py
│       │   │   ├── llm_settings.py
│       │   │   ├── milvus_settings.py
│       │   │   ├── redis_settings.py
│       │   │   └── settings.py
│       │   │
│       │   ├── embeddings/            # Embedding Services
│       │   │   ├── embedding_service_wrapper.py  # ✨ NEW: Cache #2 wrapper
│       │   │   ├── onnx_embeddings.py              # Base ONNX embeddings
│       │   │   ├── onnx_service_embedding.py       # ONNX service adapter
│       │   │   └── triton_embedding_service.py   # Triton adapter
│       │   │
│       │   ├── guardrails/            # Guardrails
│       │   │   └── guardrails_service.py
│       │   │
│       │   ├── health/                 # Health Check
│       │   │   └── health_repository.py
│       │   │
│       │   ├── llm/                    # LLM Services
│       │   │   ├── litellm_client.py   # Legacy: LiteLLM với tool calling
│       │   │   └── litellm_service.py  # ✨ NEW: ChatLiteLLM service
│       │   │
│       │   ├── logging/                # Logging
│       │   │   └── file_log_repository.py
│       │   │
│       │   ├── milvus/                 # Milvus Vector Store
│       │   │   ├── milvus_repository.py    # Milvus repository
│       │   │   └── milvus_retriever.py     # ✨ NEW: Retriever adapter
│       │   │
│       │   ├── observability/          # Observability
│       │   │   └── langfuse_service.py
│       │   │
│       │   ├── postgresql/             # PostgreSQL
│       │   │   ├── database.py
│       │   │   └── system_log_repository.py
│       │   │
│       │   ├── redis/                   # Redis Caching (4-layer strategy)
│       │   │   ├── __init__.py
│       │   │   ├── answer_cache.py              # Legacy: Answer cache
│       │   │   ├── cached_embeddings.py         # Legacy: Cached embeddings
│       │   │   ├── cached_retriever.py          # Legacy: Cached retriever
│       │   │   ├── context_cache.py              # Legacy: Context cache
│       │   │   ├── redis_text_cache.py          # ✨ NEW: Cache #1 (KV)
│       │   │   ├── redis_vector_cache.py        # ✨ NEW: Cache #3 (KV)
│       │   │   └── redis_semantic_cache.py      # ✨ NEW: Cache #4 (HNSW)
│       │   │
│       │   └── shopping_cart/          # Shopping Cart
│       │       └── shopping_cart_service.py
│       │
│       └── presentation/              # 🎨 Presentation Layer (API)
│           │
│           ├── controllers/            # Controllers
│           │   ├── __init__.py
│           │   ├── chat_controller.py
│           │   ├── document_controller.py
│           │   └── health_controller.py
│           │
│           ├── llm/                     # LLM Tools
│           │   └── search_tool.py
│           │
│           └── routers/                 # FastAPI Routers
│               ├── __init__.py
│               ├── chat_router.py
│               ├── document_router.py
│               └── health_router.py
│
├── chatbot-ceramic-tiles/              # Legacy codebase (reference)
│   ├── chat-backend/
│   ├── documents/
│   ├── rag-ops/
│   └── Scripts/
│
├── ci/                                  # CI/CD
│   ├── Jenkinsfile
│   └── scripts/
│
├── db/                                  # Database configs
│   ├── milvus/
│   └── postgresql/
│
├── deploy/                              # Deployment scripts
│   ├── dev/
│   ├── prod/
│   └── stagging/
│
├── docker/                              # Docker configs
│   ├── docker-compose.dev.yml
│   ├── docker-compose.prod.yml
│   ├── docker-compose.staging.yml
│   ├── Dockerfile
│   └── requirements.txt
│
├── docs/                                 # 📚 Documentation
│   ├── PROJECT_STRUCTURE.md            # ✨ NEW: Cấu trúc dự án
│   ├── PROJECT_STRUCTURE_TREE.md       # ✨ NEW: Cây thư mục
│   ├── REFACTOR_4_LAYER_CACHING.md     # ✨ NEW: 4-layer caching
│   ├── ANALYSIS_REPORT.md
│   ├── APPLICATION_LAYER_CHECK.md
│   └── ... (other docs)
│
├── mlops/                                # MLOps
│   ├── mlfow/
│   ├── onnx-service/
│   └── triton/
│
├── scripts/                              # Utility scripts
│   ├── ingest_collection_docs.py
│   └── ingest_company_docs.py
│
├── LICENSE
└── README.md
```

## Legend

- ✨ **NEW**: Files mới được thêm trong refactoring 4-layer caching
- 🚀 **Bootstrap**: Application startup
- 🏛️ **Domain**: Business logic layer
- 📋 **Application**: Use cases layer
- 🔧 **Infrastructure**: Implementations layer
- 🎨 **Presentation**: API layer
- 📚 **Documentation**: Docs folder

## Key Components

### 4-Layer Caching Components (NEW)

1. **Domain Interfaces** (`domain/interfaces/`)
   - 6 interfaces cho caching strategy

2. **Cache Implementations** (`infrastructure/redis/`)
   - `redis_text_cache.py` - Cache #1
   - `redis_vector_cache.py` - Cache #3
   - `redis_semantic_cache.py` - Cache #4

3. **Embedding Service** (`infrastructure/embeddings/`)
   - `embedding_service_wrapper.py` - Cache #2

4. **Domain Orchestrator** (`domain/services/`)
   - `answer_cache_facade.py` - Quản lý 4-layer pipeline

5. **Application Service** (`application/use_cases/`)
   - `chat_service.py` - High-level chat logic

6. **Infrastructure Services**
   - `litellm_service.py` - LiteLLM với ChatLiteLLM
   - `milvus_retriever.py` - Retriever adapter

## File Count Summary

- **Domain Layer**: ~20 files
- **Application Layer**: ~15 files
- **Infrastructure Layer**: ~40 files
- **Presentation Layer**: ~10 files
- **Total**: ~85 files trong `app/src/`

