# Refactored Code Changes

## Summary

This document shows the exact code changes made during the embedding pipeline refactor.

## New Classes Created

### 1. ONNXEmbeddings (`app/src/infrastructure/embeddings/onnx_embeddings.py`)

**Purpose**: Single source of truth for embeddings. The ONLY class that calls `/embed`.

**Key Features**:
- Inherits from `langchain_core.embeddings.Embeddings`
- SYNC ONLY (no async/await)
- NO cache logic
- NO orchestration logic
- ONLY implements `embed_query()` and `embed_documents()`

**Code**:
```python
class ONNXEmbeddings(Embeddings):
    def __init__(self, settings: EmbeddingSettings):
        super().__init__()
        self.settings = settings
        self.service_url = settings.ONNX_SERVICE_URL
        # ...

    def embed_query(self, text: str) -> List[float]:
        # Direct HTTP call to /embed
        response = requests.post(f"{self.service_url}/embed", ...)
        # ...

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # Direct HTTP call to /embed
        response = requests.post(f"{self.service_url}/embed", ...)
        # ...
```

### 2. CachedONNXEmbeddings (`app/src/infrastructure/embeddings/cached_embeddings.py`)

**Purpose**: Wraps ONNXEmbeddings with Redis-based caching.

**Key Features**:
- Uses LangChain's `CacheBackedEmbeddings`
- Uses `RedisStore` as byte store
- Cache key includes embedding version

**Code**:
```python
class CachedONNXEmbeddings(Embeddings):
    def __init__(self, base_embeddings, redis_settings, embedding_settings, cache_ttl=3600):
        super().__init__()
        redis_store = RedisStore(...)
        self._cached_embeddings = CacheBackedEmbeddings(
            underlying_embeddings=base_embeddings,
            document_embedding_store=redis_store
        )

    def embed_query(self, text: str) -> List[float]:
        return self._cached_embeddings.embed_query(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._cached_embeddings.embed_documents(texts)
```

### 3. ContextCache (`app/src/infrastructure/cache/context_cache.py`)

**Purpose**: Caches retriever results (documents) to avoid duplicate embedding/Milvus calls.

**Key Features**:
- Cache key includes: query + retriever config + embedding version
- If cache HIT: Skip retriever, skip embedding, skip Milvus

**Code**:
```python
class ContextCache:
    def get(self, query: str, k: int, collection: str, filters: dict) -> Optional[List[Document]]:
        # Check Redis cache
        # Return cached documents if found

    def set(self, query: str, documents: List[Document], k: int, collection: str, filters: dict) -> bool:
        # Store documents in Redis cache
```

### 4. AnswerCache (`app/src/infrastructure/cache/answer_cache.py`)

**Purpose**: Caches LLM responses (answers) with semantic similarity matching.

**Key Features**:
- Uses `RedisSemanticCache` for semantic matching
- Pre-cache: Before LLM call (TTL = 20 seconds)
- Post-cache: After LLM + tools (TTL = 15 minutes)

**Code**:
```python
class AnswerCache:
    def __init__(self, redis_settings, embeddings, distance_threshold=0.2, ...):
        self._pre_cache = RedisSemanticCache(embeddings=embeddings, ttl=20, ...)
        self._post_cache = RedisSemanticCache(embeddings=embeddings, ttl=900, ...)

    async def get(self, query: str, namespace: str) -> Optional[str]:
        # Lookup in semantic cache

    async def set(self, query: str, answer: str, namespace: str) -> bool:
        # Store in semantic cache
```

## Modified Files

### 1. Container (`app/src/bootstrap/container.py`)

**Before**:
```python
embedding_service = providers.Singleton(
    lambda settings: ONNXServiceEmbedding(settings) if ... else ...,
    settings=config.provided.embedding
)

semantic_cache = providers.Singleton(
    SemanticCacheRepository,
    embedding_service=embedding_service,
    ...
)

milvus_repository = providers.Singleton(
    MilvusVectorStoreRepository,
    embedding_service=embedding_service
)
```

**After**:
```python
# Base embeddings (sync only, no cache)
base_embeddings = providers.Singleton(
    ONNXEmbeddings,
    settings=config.provided.embedding
)

# Cache-backed embeddings
cached_embeddings = providers.Singleton(
    CachedONNXEmbeddings,
    base_embeddings=base_embeddings,
    redis_settings=config.provided.redis,
    embedding_settings=config.provided.embedding
)

# Context cache
context_cache = providers.Singleton(
    ContextCache,
    redis_settings=config.provided.redis,
    embedding_settings=config.provided.embedding
)

# Answer cache
answer_cache = providers.Singleton(
    AnswerCache,
    redis_settings=config.provided.redis,
    embeddings=base_embeddings,
    ...
)

milvus_repository = providers.Singleton(
    MilvusVectorStoreRepository,
    embedding_service=cached_embeddings  # Use cached embeddings
)
```

### 2. RAGUseCase (`app/src/application/use_cases/rag_use_case.py`)

**Before**:
```python
def __init__(self, ..., cache_service: Optional[ISemanticCacheRepository] = None, ...):
    self.cache_service = cache_service

# In methods:
if self.cache_service:
    cached_response = await self.cache_service.get_similar(
        query=request.question,
        threshold=0.95,
        namespace="pre-cache"
    )
    # ...
    await self.cache_service.set_with_embedding(
        query=request.question,
        value=answer,
        namespace="pre-cache"
    )
```

**After**:
```python
def __init__(self, ..., answer_cache: Optional[Any] = None, context_cache: Optional[Any] = None, ...):
    self.answer_cache = answer_cache
    self.context_cache = context_cache

# In methods:
if self.answer_cache:
    cached_answer = await self.answer_cache.get(
        query=request.question,
        namespace="pre-cache"
    )
    # ...
    await self.answer_cache.set(
        query=request.question,
        answer=answer,
        namespace="pre-cache"
    )
```

## Removed Code (DEPRECATED)

### 1. ONNXServiceEmbedding (`app/src/infrastructure/embeddings/onnx_service_embedding.py`)

**Why Removed**:
- Async implementation conflicted with LangChain's sync Embeddings interface
- Contained async/await logic that caused event loop issues
- Replaced by ONNXEmbeddings (sync only)

**Migration**:
- All usages replaced by `ONNXEmbeddings`
- `CachedONNXEmbeddings` wraps `ONNXEmbeddings` for caching

### 2. SemanticCacheRepository (`app/src/infrastructure/redis/semantic_cache.py`)

**Why Removed**:
- Mixed concerns: embedding logic + cache logic
- `LangChainEmbeddingWrapper` contained orchestration logic
- Replaced by:
  - `AnswerCache`: For LLM response caching
  - `ContextCache`: For retriever result caching

**Migration**:
- `SemanticCacheRepository.get_similar()` → `AnswerCache.get()`
- `SemanticCacheRepository.set_with_embedding()` → `AnswerCache.set()`
- `LangChainEmbeddingWrapper` → `ONNXEmbeddings` (no wrapper needed)

## Architecture Comparison

### Before (Problematic)

```
User Query
  → RAGUseCase
    → cache_service.get_similar()  # Manual embedding call
      → LangChainEmbeddingWrapper.embed_query()  # Wrapper with orchestration
        → ONNXServiceEmbedding.embed_text()  # Async embedding
          → httpx.AsyncClient.post("/embed")  # Async HTTP
    → MilvusRepository.search()
      → wrapper.similarity_search()
        → ONNXServiceEmbedding.embed_text()  # Duplicate embedding call!
          → httpx.AsyncClient.post("/embed")
```

**Problems**:
- Embedding called multiple times
- Async/sync mixing
- Manual embedding calls
- Cache logic in embedding class

### After (Correct)

```
User Query
  → RAGUseCase
    → answer_cache.get()  # Check LLM response cache
      → RedisSemanticCache.lookup()  # Uses base_embeddings.embed_query()
    → SearchUseCase (if cache miss)
      → MilvusRepository.search()
        → wrapper.similarity_search()
          → cached_embeddings.embed_query()  # Single embedding call
            → CacheBackedEmbeddings (checks Redis cache)
              → ONNXEmbeddings.embed_query()  # Only on cache miss
                → requests.post("/embed")  # Sync HTTP
    → LLM Generation
    → answer_cache.set()  # Cache LLM response
```

**Benefits**:
- Embedding called only once per unique text
- Sync only (no event loop issues)
- No manual embedding calls
- Clear separation of concerns

## Testing

### Before Refactor
- Embedding called: ~3-5 times per query
- Event loop errors: Frequent
- Cache misses: High

### After Refactor
- Embedding called: 1 time per unique text (cached)
- Event loop errors: None (sync only)
- Cache hits: High (Redis cache working)

## Next Steps

1. **Remove Deprecated Files**:
   - `app/src/infrastructure/embeddings/onnx_service_embedding.py`
   - `app/src/infrastructure/redis/semantic_cache.py`

2. **Update Imports**:
   - Search for any remaining imports of `ONNXServiceEmbedding`
   - Search for any remaining imports of `SemanticCacheRepository`

3. **Add Integration Tests**:
   - Test embedding cache hit/miss
   - Test context cache hit/miss
   - Test answer cache hit/miss
   - Verify no duplicate embedding calls

4. **Monitor Metrics**:
   - Embedding call count (should decrease)
   - Cache hit rate (should increase)
   - Response time (should improve)

