# 4-Layer Caching Strategy - Refactoring Summary

## Overview

This document describes the refactoring of the chatbot into a production-grade RAG system following **Clean Architecture (CA)**, **Dependency Injection (DI)**, and a **Strict 4-Layer Caching Strategy**.

## Architecture Overview

### Layer Organization

1. **Domain Layer** (`app/src/domain/`)
   - Interfaces: `ITextCache`, `IEmbeddingService`, `IVectorCache`, `ISemanticCache`, `IRetriever`, `ILLMService`
   - Services: `AnswerCacheFacade` (domain orchestrator)

2. **Application Layer** (`app/src/application/`)
   - Use Cases: `ChatService` (high-level logic)

3. **Infrastructure Layer** (`app/src/infrastructure/`)
   - Implementations: `RedisTextCache`, `RedisVectorCache`, `RedisSemanticCache`, `LiteLLMService`, `MilvusRetriever`, `EmbeddingServiceWrapper`

## 4-Layer Caching Strategy

### Cache #1: Exact Text Answer (KV)
- **Key**: `answer:text:{hash(normalized_text)}`
- **Implementation**: `RedisTextCache` (Redis KV storage)
- **Purpose**: Fast exact match for identical queries
- **Hit**: Return Answer (Stop)

### Cache #2: Embedding Cache (Internal)
- **Key**: `embedding:{hash(normalized_text)}`
- **Implementation**: `CachedONNXEmbeddings` (wrapped by `EmbeddingServiceWrapper`)
- **Purpose**: **ONLY** place where `/embed` is called
- **Hit**: Return `query_vector`. **Miss**: Call Embedding API -> Save -> Return `query_vector`

### Cache #3: Exact Embedding Answer (KV)
- **Key**: `answer:emb:{hash(query_vector)}`
- **Implementation**: `RedisVectorCache` (Redis KV storage)
- **Purpose**: Fast exact match for identical embeddings
- **Hit**: Return Answer (Stop)

### Cache #4: Semantic Cache (Redis HNSW)
- **Index**: `idx:answer:semantic` (HNSW)
- **Implementation**: `RedisSemanticCache` (Redis Vector Search)
- **Purpose**: KNN search for semantically similar queries
- **Hit**: Retrieve `answer_id` -> Get Payload -> Return Answer (Stop)

## Runtime Pipeline (Immutable Order)

### Step 0: Input Guardrails (Normalization)
- **Input**: `raw_text` -> **Output**: `normalized_text`
- **Logic**: Lowercase, trim, whitespace normalization

### Step 1: Cache #1 - Exact Text Answer (KV)
- Check: `answer:text:{hash(normalized_text)}`
- **Hit**: Return Answer (Stop)

### Step 2: Cache #2 - Embedding Cache (Internal)
- Check: `embedding:{hash(normalized_text)}`
- **Hit**: Return `query_vector`
- **Miss**: Call `/embed` API -> Save -> Return `query_vector`

### Step 3: Cache #3 - Exact Embedding Answer (KV)
- Check: `answer:emb:{hash(query_vector)}`
- **Hit**: Return Answer (Stop)

### Step 4: Cache #4 - Semantic Cache (Redis HNSW)
- KNN search using `query_vector`
- Apply `similarity_threshold`
- **Hit**: Retrieve `answer_id` -> Get Payload -> Return Answer (Stop)

### Step 5: Fallback - RAG Core
- **Retriever**: `MilvusRetriever.invoke(query_vector)`
- **Generator**: `LiteLLMService.invoke(prompt)` using `"groq"` model
- **Output Guardrails**: Final safety check

### Step 6: Write-Back Logic (Post-Generation)
After answer generation, save to:
1. **Cache #1** (Keyed by text hash)
2. **Cache #3** (Keyed by vector hash)
3. **Cache #4** (Stored in Redis Vector Search index)

## LLM & Proxy Integration

### Technical Specs
- **Client**: `ChatLiteLLM` from `langchain_community.chat_models`
- **Model Alias**: `"groq"` (as defined in `model_list` of proxy config)
- **Authentication**: `LITELLM_MASTER_KEY` (value: `"gach-llmops"`) in `openai_api_key`
- **Endpoint**: `LITELLM_PROXY_URL` in `openai_api_base`
- **Efficiency**: No retries/fallbacks (Proxy's `router_settings` handle this)

### Implementation
- **File**: `app/src/infrastructure/llm/litellm_service.py`
- **Class**: `LiteLLMService` implements `ILLMService`

## Dependency Injection

### Container Setup
All services are wired via `dependency-injector` in `app/src/bootstrap/container.py`:

```python
# Cache implementations
text_cache = providers.Singleton(RedisTextCache, ...)
vector_cache = providers.Singleton(RedisVectorCache, ...)
semantic_cache = providers.Singleton(RedisSemanticCache, ...)

# Embedding service (Cache #2)
embedding_service = providers.Singleton(EmbeddingServiceWrapper, ...)

# Retriever
retriever = providers.Singleton(MilvusRetriever, ...)

# LLM service
llm_service = providers.Singleton(LiteLLMService, ...)

# Domain orchestrator
cache_facade = providers.Factory(AnswerCacheFacade, ...)

# Application service
chat_service = providers.Factory(ChatService, ...)
```

## Environment Configuration

### Required Environment Variables
```env
# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# LiteLLM Proxy
LITELLM_BASE_URL=http://localhost:4000
LITELLM_API_KEY=gach-llmops
LLM_MODEL=groq

# Embedding Service
ONNX_SERVICE_URL=http://localhost:7000
EMBEDDING_DIMENSION=768

# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

## Technical Invariants

1. **Environment**: All configs read from `.env`
2. **Redis**: Use **DB 0** only. Differentiate layers using prefixes
3. **Concurrency**: Synchronous calls (async wrapper for compatibility)
4. **LangChain**: Maintain compatibility with `BaseChatModel` and `VectorStore` patterns

## File Structure

```
app/src/
├── domain/
│   ├── interfaces/
│   │   ├── text_cache_interface.py
│   │   ├── embedding_service_interface.py
│   │   ├── vector_cache_interface.py
│   │   ├── semantic_cache_interface.py
│   │   ├── retriever_interface.py
│   │   └── llm_service_interface.py
│   └── services/
│       └── answer_cache_facade.py
├── application/
│   └── use_cases/
│       └── chat_service.py
└── infrastructure/
    ├── redis/
    │   ├── redis_text_cache.py (Cache #1)
    │   ├── redis_vector_cache.py (Cache #3)
    │   └── redis_semantic_cache.py (Cache #4)
    ├── embeddings/
    │   └── embedding_service_wrapper.py (Cache #2)
    ├── llm/
    │   └── litellm_service.py
    └── milvus/
        └── milvus_retriever.py
```

## Usage Example

```python
# In controller or router
from app.src.application.use_cases.chat_service import ChatService
from app.src.application.dto.chat_dto import ChatRequestDTO

# ChatService is injected via DI container
chat_service: ChatService = container.chat_service()

# Process chat request
request = ChatRequestDTO(
    question="What are your ceramic tile collections?",
    session_id="session_123",
    user_id="user_456"
)

response = await chat_service.process_chat(request)
# Response includes cache_hit metadata
```

## Next Steps

1. Update DI container to wire all services
2. Add integration tests for 4-layer caching
3. Add monitoring/metrics for cache hit rates
4. Optimize similarity threshold based on production data

