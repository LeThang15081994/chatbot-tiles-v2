# Legacy Code Isolation Guide

## Overview

This document describes the isolation strategy for legacy code to ensure Clean Architecture compliance while preserving all existing functionality.

## Isolation Strategy

### Principle
- **Preserve**: All legacy files are preserved (no deletion)
- **Isolate**: Legacy code is not used in the new 4-layer caching pipeline
- **Maintain**: Legacy functionality remains available for backward compatibility

---

## Legacy Files Inventory

### Application Layer

#### `application/use_cases/rag_use_case.py`
- **Status**: Legacy, isolated
- **Purpose**: RAG with tool calling (LangChain tools)
- **Used By**: Legacy controllers/routers
- **Replacement**: `application/use_cases/chat_service.py` (new 4-layer caching)
- **Isolation**: Not imported in new pipeline

#### `application/interfaces/*`
- **Status**: Legacy, isolated
- **Purpose**: Application layer interfaces (old architecture)
- **Replacement**: `domain/interfaces/*` (new domain interfaces)
- **Isolation**: Not used in new pipeline

---

### Infrastructure Layer - LLM

#### `infrastructure/llm/litellm_client.py`
- **Status**: Legacy, isolated
- **Purpose**: LiteLLM client with tool calling support
- **Used By**: `rag_use_case.py` (legacy)
- **Replacement**: `infrastructure/llm/litellm_service.py` (new, implements `ILLMService`)
- **Isolation**: Not imported in new pipeline
- **Note**: Uses `ChatOpenAI` from `langchain_openai`

---

### Infrastructure Layer - Embeddings

#### `infrastructure/embeddings/onnx_service_embedding.py`
- **Status**: Legacy, isolated
- **Purpose**: ONNX service embedding adapter (async)
- **Has**: `/embed` API calls
- **Replacement**: `infrastructure/embeddings/embedding_service_wrapper.py` (new)
- **Isolation**: Not used in new pipeline
- **Note**: This file has `/embed` calls but is NOT in the new pipeline

#### `infrastructure/embeddings/triton_embedding_service.py`
- **Status**: Legacy, isolated
- **Purpose**: Triton embedding service adapter
- **Has**: `/embed` API calls
- **Replacement**: `infrastructure/embeddings/embedding_service_wrapper.py` (new)
- **Isolation**: Not used in new pipeline
- **Note**: This file has `/embed` calls but is NOT in the new pipeline

#### `infrastructure/embeddings/onnx_embeddings.py`
- **Status**: ✅ ACTIVE (used in new pipeline)
- **Purpose**: Base ONNX embeddings (sync, calls `/embed`)
- **Used By**: `CachedONNXEmbeddings` → `EmbeddingServiceWrapper`
- **Note**: This is the **ONLY** file that calls `/embed` in the new pipeline

---

### Infrastructure Layer - Redis Caching

#### `infrastructure/redis/answer_cache.py`
- **Status**: Legacy, isolated
- **Purpose**: Answer cache using RedisSemanticCache
- **Used By**: `rag_use_case.py` (legacy)
- **Replacement**: New 4-layer caching strategy
- **Isolation**: Not imported in new pipeline

#### `infrastructure/redis/cached_embeddings.py`
- **Status**: ✅ ACTIVE (used in new pipeline)
- **Purpose**: Cache-backed embeddings (wraps ONNXEmbeddings)
- **Used By**: `EmbeddingServiceWrapper` (new pipeline)
- **Note**: This is part of Cache #2 in the new pipeline

#### `infrastructure/redis/cached_retriever.py`
- **Status**: Legacy, isolated
- **Purpose**: Cached retriever wrapper
- **Used By**: Legacy code
- **Replacement**: New retriever via `IRetriever` interface
- **Isolation**: Not imported in new pipeline

#### `infrastructure/redis/context_cache.py`
- **Status**: Legacy, isolated
- **Purpose**: Context cache for retriever results
- **Used By**: Legacy code
- **Replacement**: New 4-layer caching strategy
- **Isolation**: Not imported in new pipeline

---

## New Pipeline Files

### Domain Layer
- ✅ `domain/interfaces/*` - New domain interfaces
- ✅ `domain/services/answer_cache_facade.py` - Domain orchestrator

### Application Layer
- ✅ `application/use_cases/chat_service.py` - New chat service

### Infrastructure Layer
- ✅ `infrastructure/redis/redis_text_cache.py` - Cache #1
- ✅ `infrastructure/redis/redis_vector_cache.py` - Cache #3
- ✅ `infrastructure/redis/redis_semantic_cache.py` - Cache #4
- ✅ `infrastructure/embeddings/embedding_service_wrapper.py` - Cache #2
- ✅ `infrastructure/llm/litellm_service.py` - New LLM service
- ✅ `infrastructure/milvus/milvus_retriever.py` - New retriever

---

## /embed Call Verification

### ✅ New Pipeline (Single Call Path)
```
AnswerCacheFacade
  → EmbeddingServiceWrapper.embed_query()
    → CachedONNXEmbeddings.embed_query()
      → ONNXEmbeddings.embed_query()
        → requests.post("/embed")  ← ONLY CALL SITE
```

### ❌ Legacy Files (Isolated, Not in Pipeline)
- `onnx_service_embedding.py` - Has `/embed` but NOT used
- `triton_embedding_service.py` - Has `/embed` but NOT used

**Verification**: `/embed` is called **ONLY ONCE** in the new pipeline through the single path above.

---

## Migration Path

### For New Features
- Use `ChatService` (new pipeline with 4-layer caching)
- Inject via `AnswerCacheFacade`

### For Legacy Features
- Continue using `RAGUseCase` (legacy pipeline)
- Both pipelines can coexist

### For Embedding Calls
- **New**: Use `EmbeddingServiceWrapper` (via `IEmbeddingService` interface)
- **Legacy**: Continue using legacy embedding services (isolated)

---

## Backward Compatibility

### Preserved Functionality
- ✅ All legacy use cases remain functional
- ✅ All legacy controllers/routers remain functional
- ✅ All legacy services remain functional
- ✅ No breaking changes to existing APIs

### New Functionality
- ✅ New 4-layer caching pipeline
- ✅ New domain interfaces
- ✅ New infrastructure implementations
- ✅ Clean Architecture compliance

---

## Testing Strategy

### New Pipeline Tests
- Test `ChatService` with 4-layer caching
- Test each cache layer independently
- Test pipeline order (immutable)
- Test `/embed` is called only once

### Legacy Pipeline Tests
- Continue testing `RAGUseCase`
- Test legacy embedding services
- Test legacy caching strategies

### Integration Tests
- Test both pipelines can coexist
- Test no cross-contamination between pipelines
- Test backward compatibility

---

## Summary

| Category | Status | Count |
|----------|--------|-------|
| Legacy Files (Isolated) | ✅ | 8 files |
| New Pipeline Files | ✅ | 10 files |
| /embed Call Sites (New) | ✅ | 1 path |
| /embed Call Sites (Legacy) | ⚠️ | 2 files (isolated) |
| Breaking Changes | ✅ | 0 |
| Backward Compatibility | ✅ | 100% |

---

## Notes

1. **Legacy files are preserved** - No files deleted
2. **Legacy files are isolated** - Not imported in new pipeline
3. **New pipeline is clean** - Follows Clean Architecture strictly
4. **Both pipelines coexist** - No conflicts
5. **Migration is optional** - Legacy code can remain indefinitely

