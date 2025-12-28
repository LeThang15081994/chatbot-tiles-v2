# Cấu Trúc Dự Án - Chatbot Tiles v2.0

## Tổng Quan

Dự án được tổ chức theo **Clean Architecture** với 4 lớp chính:
1. **Domain Layer** - Business logic và interfaces
2. **Application Layer** - Use cases và DTOs
3. **Infrastructure Layer** - Implementations và adapters
4. **Presentation Layer** - Controllers và routers

## Cấu Trúc Thư Mục

```
app/src/
├── bootstrap/                    # Application startup và DI container
│   ├── container.py              # Dependency Injection container
│   └── main.py                   # FastAPI application entry point
│
├── domain/                        # Domain Layer (Business Logic)
│   ├── entities/                 # Domain entities
│   │   ├── chat_session.py
│   │   ├── conversation_history.py
│   │   ├── document.py
│   │   ├── embedding_model.py
│   │   ├── message.py
│   │   ├── retrieval_result.py
│   │   └── tool_call.py
│   │
│   ├── interfaces/               # Domain interfaces (mới - 4-layer caching)
│   │   ├── __init__.py
│   │   ├── text_cache_interface.py        # ITextCache (Cache #1)
│   │   ├── embedding_service_interface.py  # IEmbeddingService (Cache #2)
│   │   ├── vector_cache_interface.py       # IVectorCache (Cache #3)
│   │   ├── semantic_cache_interface.py     # ISemanticCache (Cache #4)
│   │   ├── retriever_interface.py          # IRetriever
│   │   └── llm_service_interface.py         # ILLMService
│   │
│   ├── services/                 # Domain services
│   │   ├── answer_cache_facade.py          # Domain orchestrator (4-layer caching)
│   │   ├── context_builder.py
│   │   ├── conversation_manager.py
│   │   ├── prompt_builder.py
│   │   ├── retrieval_optimizer.py
│   │   └── summarize_service.py
│   │
│   └── value_objects/            # Value objects
│       ├── context.py
│       ├── llm_config.py
│       ├── prompt.py
│       ├── query.py
│       ├── retrieval_config.py
│       ├── search_filter.py
│       ├── session_id.py
│       └── user_id.py
│
├── application/                   # Application Layer (Use Cases)
│   ├── dto/                      # Data Transfer Objects
│   │   ├── chat_dto.py
│   │   ├── document_dto.py
│   │   ├── health_dto.py
│   │   ├── search_dto.py
│   │   └── system_log_dto.py
│   │
│   ├── interfaces/               # Application interfaces (legacy)
│   │   ├── cache_repository.py
│   │   ├── embedding_repository.py
│   │   ├── health_repository.py
│   │   ├── llm_repository.py
│   │   ├── system_log_repository.py
│   │   └── vector_store_repository.py
│   │
│   └── use_cases/                # Use cases
│       ├── chat_service.py        # NEW: High-level chat với 4-layer caching
│       ├── health_check_use_case.py
│       ├── rag_use_case.py        # Legacy: RAG với tool calling
│       ├── search_use_case.py
│       └── system_log_use_case.py
│
├── infrastructure/                # Infrastructure Layer (Implementations)
│   ├── config/                   # Configuration settings
│   │   ├── database_settings.py
│   │   ├── embedding_settings.py
│   │   ├── env.example
│   │   ├── guardrails_settings.py
│   │   ├── langfuse_settings.py
│   │   ├── llm_settings.py
│   │   ├── milvus_settings.py
│   │   ├── redis_settings.py
│   │   └── settings.py
│   │
│   ├── embeddings/               # Embedding services
│   │   ├── embedding_service_wrapper.py    # NEW: Wrapper cho Cache #2
│   │   ├── onnx_embeddings.py              # Base ONNX embeddings
│   │   ├── onnx_service_embedding.py       # ONNX service adapter
│   │   └── triton_embedding_service.py     # Triton adapter
│   │
│   ├── guardrails/               # Guardrails service
│   │   └── guardrails_service.py
│   │
│   ├── health/                   # Health check
│   │   └── health_repository.py
│   │
│   ├── llm/                      # LLM services
│   │   ├── litellm_client.py    # Legacy: LiteLLM client với tool calling
│   │   └── litellm_service.py   # NEW: LiteLLM service (ChatLiteLLM)
│   │
│   ├── logging/                  # Logging
│   │   └── file_log_repository.py
│   │
│   ├── milvus/                   # Milvus vector store
│   │   ├── milvus_repository.py            # Milvus repository
│   │   └── milvus_retriever.py             # NEW: Milvus retriever adapter
│   │
│   ├── observability/           # Observability
│   │   └── langfuse_service.py
│   │
│   ├── postgresql/               # PostgreSQL database
│   │   ├── database.py
│   │   └── system_log_repository.py
│   │
│   ├── redis/                    # Redis caching (4-layer strategy)
│   │   ├── __init__.py
│   │   ├── answer_cache.py                  # Legacy: Answer cache
│   │   ├── cached_embeddings.py             # Legacy: Cached embeddings
│   │   ├── cached_retriever.py              # Legacy: Cached retriever
│   │   ├── context_cache.py                  # Legacy: Context cache
│   │   ├── redis_text_cache.py              # NEW: Cache #1 - Exact text KV
│   │   ├── redis_vector_cache.py            # NEW: Cache #3 - Exact embedding KV
│   │   └── redis_semantic_cache.py          # NEW: Cache #4 - HNSW semantic
│   │
│   └── shopping_cart/            # Shopping cart service
│       └── shopping_cart_service.py
│
└── presentation/                  # Presentation Layer (API)
    ├── controllers/              # Controllers
    │   ├── __init__.py
    │   ├── chat_controller.py
    │   ├── document_controller.py
    │   └── health_controller.py
    │
    ├── llm/                      # LLM tools
    │   └── search_tool.py
    │
    └── routers/                   # FastAPI routers
        ├── __init__.py
        ├── chat_router.py
        ├── document_router.py
        └── health_router.py
```

## Kiến Trúc 4-Layer Caching

### Cache #1: Exact Text Answer (KV)
- **File**: `infrastructure/redis/redis_text_cache.py`
- **Interface**: `domain/interfaces/text_cache_interface.py`
- **Key Format**: `answer:text:{hash(normalized_text)}`
- **Purpose**: Fast exact match cho queries giống hệt nhau

### Cache #2: Embedding Cache (Internal)
- **File**: `infrastructure/embeddings/embedding_service_wrapper.py`
- **Interface**: `domain/interfaces/embedding_service_interface.py`
- **Key Format**: `embedding:{hash(normalized_text)}`
- **Purpose**: **DUY NHẤT** nơi gọi `/embed` API
- **Implementation**: Wraps `CachedONNXEmbeddings`

### Cache #3: Exact Embedding Answer (KV)
- **File**: `infrastructure/redis/redis_vector_cache.py`
- **Interface**: `domain/interfaces/vector_cache_interface.py`
- **Key Format**: `answer:emb:{hash(query_vector)}`
- **Purpose**: Fast exact match cho embeddings giống hệt nhau

### Cache #4: Semantic Cache (HNSW)
- **File**: `infrastructure/redis/redis_semantic_cache.py`
- **Interface**: `domain/interfaces/semantic_cache_interface.py`
- **Index**: `idx:answer:semantic` (HNSW)
- **Purpose**: KNN search cho queries tương tự về ngữ nghĩa

## Domain Orchestrator

### AnswerCacheFacade
- **File**: `domain/services/answer_cache_facade.py`
- **Role**: Domain orchestrator quản lý flow giữa 4 cache layers
- **Pipeline**:
  1. Step 0: Input normalization
  2. Step 1: Cache #1 check
  3. Step 2: Cache #2 (embedding generation)
  4. Step 3: Cache #3 check
  5. Step 4: Cache #4 (semantic search)
  6. Step 5: RAG Core (Milvus + LLM)
  7. Step 6: Write-back to all caches

## Application Services

### ChatService
- **File**: `application/use_cases/chat_service.py`
- **Role**: High-level chat logic
- **Dependencies**:
  - `AnswerCacheFacade` (domain orchestrator)
  - `ILLMService` (via interface)

### RAGUseCase (Legacy)
- **File**: `application/use_cases/rag_use_case.py`
- **Role**: RAG với tool calling (giữ lại cho backward compatibility)

## Infrastructure Services

### LiteLLM Service
- **File**: `infrastructure/llm/litellm_service.py`
- **Implementation**: `ChatLiteLLM` from `langchain_community`
- **Model**: `"groq"` (alias từ proxy config)
- **Auth**: `LITELLM_MASTER_KEY` = `"gach-llmops"`

### Milvus Retriever
- **File**: `infrastructure/milvus/milvus_retriever.py`
- **Role**: Vector-based document retrieval
- **Wrapper**: Around `MilvusVectorStoreRepository`

## Dependency Flow

```
Presentation Layer (Routers/Controllers)
    ↓
Application Layer (Use Cases)
    ↓
Domain Layer (Services/Interfaces)
    ↓
Infrastructure Layer (Implementations)
```

## Dependency Injection

- **Container**: `bootstrap/container.py`
- **Framework**: `dependency-injector`
- **Wiring**: Tất cả services được wire qua container

## Configuration

- **Settings**: `infrastructure/config/settings.py`
- **Environment**: `.env` file (template: `infrastructure/config/env.example`)
- **Components**:
  - Redis settings
  - LiteLLM settings
  - Embedding settings
  - Milvus settings
  - Guardrails settings
  - Langfuse settings

## Key Files Summary

### Mới Thêm (4-Layer Caching)
1. `domain/interfaces/*` - 6 domain interfaces
2. `domain/services/answer_cache_facade.py` - Domain orchestrator
3. `infrastructure/redis/redis_text_cache.py` - Cache #1
4. `infrastructure/redis/redis_vector_cache.py` - Cache #3
5. `infrastructure/redis/redis_semantic_cache.py` - Cache #4
6. `infrastructure/embeddings/embedding_service_wrapper.py` - Cache #2
7. `infrastructure/llm/litellm_service.py` - LiteLLM service
8. `infrastructure/milvus/milvus_retriever.py` - Retriever adapter
9. `application/use_cases/chat_service.py` - Chat service

### Legacy (Giữ Lại)
- `application/use_cases/rag_use_case.py` - RAG với tool calling
- `infrastructure/llm/litellm_client.py` - LiteLLM client với tools
- `infrastructure/redis/answer_cache.py` - Legacy answer cache
- `infrastructure/redis/cached_embeddings.py` - Legacy cached embeddings

## Next Steps

1. **Update DI Container**: Wire tất cả services mới vào container
2. **Integration Tests**: Test 4-layer caching pipeline
3. **Migration**: Migrate từ RAGUseCase sang ChatService
4. **Monitoring**: Add metrics cho cache hit rates

## Notes

- Tất cả caches sử dụng **Redis DB 0** với prefix-based differentiation
- Embedding service là **DUY NHẤT** nơi gọi `/embed` API
- LiteLLM service sử dụng `ChatLiteLLM` với model alias `"groq"`
- Pipeline thực thi theo thứ tự cố định (immutable order)

