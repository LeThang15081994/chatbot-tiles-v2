# Embedding & Retrieval Pipeline Refactor Summary

## Overview

This document summarizes the refactoring of the embedding and retrieval pipeline to follow LangChain OSS best practices (2024-2025).

## Problems Solved

1. **Duplicate Embedding Calls**: The same query was embedded multiple times
2. **Two Embedding Classes**: `LangChainEmbeddingWrapper` and `ONNXServiceEmbedding` caused confusion
3. **Manual Embedding Calls**: Embedding was called outside of Retriever
4. **Mixed Sync/Async**: Architectural issues from mixing sync and async embedding
5. **Cache Logic in Embeddings**: Embedding class contained orchestration logic

## New Architecture

### 1. Single Embeddings Implementation

**File**: `app/src/infrastructure/embeddings/onnx_embeddings.py`

- **ONNXEmbeddings**: The ONLY Embeddings class
- Inherits from `langchain_core.embeddings.Embeddings`
- SYNC ONLY (no async/await)
- ONLY calls HTTP endpoint `/embed`
- NO cache logic
- NO orchestration logic
- ONLY implements `embed_query()` and `embed_documents()`

### 2. Cache-Backed Embeddings

**File**: `app/src/infrastructure/embeddings/cached_embeddings.py`

- **CachedONNXEmbeddings**: Wraps ONNXEmbeddings with Redis cache
- Uses LangChain's `CacheBackedEmbeddings`
- Uses `RedisStore` as byte store
- Cache key includes: normalized text + embedding version
- TTL: Configurable (default: 1 hour)

### 3. Context Cache

**File**: `app/src/infrastructure/redis/context_cache.py`

- **ContextCache**: Caches retriever results (documents)
- If cache HIT: Skip retriever, skip embedding, skip Milvus
- Cache key includes: normalized query + retriever config (k, filters, collection) + embedding version
- TTL: Configurable (default: 1 hour)
- **Location**: Moved to `redis/` folder (all Redis-related cache implementations)

### 4. Answer Cache

**File**: `app/src/infrastructure/redis/answer_cache.py`

- **AnswerCache**: Caches LLM responses (answers)
- Uses `RedisSemanticCache` for semantic similarity matching
- Pre-cache: Before LLM call (TTL = 20 seconds)
- Post-cache: After LLM + tools (TTL = 15 minutes)
- **Location**: Moved to `redis/` folder (all Redis-related cache implementations)

### 5. Pipeline Flow

```
User Query
  ↓
Answer Cache Check (pre-cache)
  ├─> HIT: Return cached answer
  └─> MISS: Continue
      ↓
Context Cache Check (optional, can be added later)
  ├─> HIT: Return cached documents (skip retriever/embedding/Milvus)
  └─> MISS: Continue
      ↓
Retriever.invoke(query)
  ↓
CacheBackedEmbeddings
  ├─> Cache HIT: Return cached embedding
  └─> Cache MISS: Continue
      ↓
ONNXEmbeddings.embed_query()
  ↓
requests.post("/embed")
  ↓
Milvus similarity search
  ↓
LLM Generation
  ↓
Answer Cache Store (pre-cache or post-cache)
```

## Key Principles

1. **Single Source of Truth**: Only ONE Embeddings class (`ONNXEmbeddings`)
2. **Embedding Only in Retriever**: Embedding is ONLY triggered inside Retriever
3. **No Manual Embedding Calls**: No `embed_query()` calls in business logic
4. **Separation of Concerns**:
   - Embeddings: Only HTTP calls to `/embed`
   - CacheBackedEmbeddings: Embedding caching
   - ContextCache: Retriever result caching
   - AnswerCache: LLM response caching
5. **Sync Only for Embeddings**: Required by LangChain interface

## Files Changed

### New Files

1. `app/src/infrastructure/embeddings/onnx_embeddings.py` - Single Embeddings implementation
2. `app/src/infrastructure/embeddings/cached_embeddings.py` - Cache wrapper
3. `app/src/infrastructure/redis/context_cache.py` - Context cache (moved to redis/ folder)
4. `app/src/infrastructure/redis/answer_cache.py` - Answer cache (moved to redis/ folder)
5. `app/src/infrastructure/retrievers/cached_retriever.py` - Cached retriever (optional, for future use)

### Modified Files

1. `app/src/bootstrap/container.py` - Updated DI wiring
2. `app/src/application/use_cases/rag_use_case.py` - Updated to use answer_cache
3. `app/src/infrastructure/embeddings/__init__.py` - Updated exports

### Files to Remove (DEPRECATED)

1. `app/src/infrastructure/embeddings/onnx_service_embedding.py` - Replaced by ONNXEmbeddings
2. `app/src/infrastructure/redis/semantic_cache.py` - Replaced by AnswerCache and ContextCache

## Migration Notes

### For MilvusRepository

- No changes needed
- Already uses `embedding_function` parameter
- LangChain Milvus wrapper calls `embedding_function.embed_query()` internally
- Now receives `CachedONNXEmbeddings` instead of `ONNXServiceEmbedding`

### For RAGUseCase

- Changed from `cache_service` to `answer_cache`
- `answer_cache.get()` replaces `cache_service.get_similar()`
- `answer_cache.set()` replaces `cache_service.set_with_embedding()`
- No more manual embedding calls

### For Container

- `base_embeddings`: ONNXEmbeddings (sync, no cache)
- `cached_embeddings`: CachedONNXEmbeddings (wraps base with Redis cache)
- `context_cache`: ContextCache (for retriever results)
- `answer_cache`: AnswerCache (for LLM responses)
- `milvus_repository`: Uses `cached_embeddings`
- Removed `semantic_cache` (replaced by `answer_cache`)

## Testing Checklist

- [ ] Embedding is called only once per unique text
- [ ] Context cache prevents duplicate retriever calls
- [ ] Answer cache prevents duplicate LLM calls
- [ ] No manual embedding calls in business logic
- [ ] Milvus search works with cached embeddings
- [ ] Redis cache is properly namespaced and versioned
- [ ] TTLs are respected for all caches

## Next Steps

1. Remove deprecated files (`onnx_service_embedding.py`, `semantic_cache.py`)
2. Add integration tests for new architecture
3. Monitor embedding call counts (should decrease significantly)
4. Consider adding context cache to SearchUseCase if needed
5. Update documentation with new architecture diagrams

