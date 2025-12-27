# Giải Thích Chức Năng Các File Cache

## Tổng Quan

Hệ thống có 4 file cache chính, mỗi file phục vụ một mục đích cụ thể:

1. **`redis_cache.py`** - Basic Redis Cache (key-value)
2. **`answer_cache.py`** - LLM Response Cache (semantic similarity)
3. **`context_cache.py`** - Retriever Result Cache (documents)
4. **`cached_embeddings.py`** - Embedding Cache (wraps ONNXEmbeddings)

---

## 1. `redis_cache.py` - Basic Redis Cache

**Vị trí**: `app/src/infrastructure/redis/redis_cache.py`

**Chức năng**:
- **Basic key-value cache** sử dụng Redis
- Implement interface `ICacheRepository`
- Cung cấp các operations cơ bản: `get`, `set`, `delete`, `exists`, `clear`, `get_ttl`
- Async operations (sử dụng `redis.asyncio`)

**Sử dụng**:
- ✅ **Đang được sử dụng** trong `HealthRepository` để check Redis health
- ✅ Inject vào `health_repository` trong Container
- ✅ Dùng cho health check và basic caching needs

**Ví dụ sử dụng**:
```python
# Trong HealthRepository
await self.cache.health_check()  # Check Redis connection
```

**Kết luận**: ✅ **GIỮ LẠI** - Vẫn được sử dụng

---

## 2. `answer_cache.py` - LLM Response Cache

**Vị trí**: `app/src/infrastructure/redis/answer_cache.py`

**Chức năng**:
- **Cache LLM responses (answers)** với semantic similarity matching
- Sử dụng `RedisSemanticCache` từ LangChain
- Hỗ trợ 2 namespaces:
  - **Pre-cache**: Trước khi gọi LLM (TTL = 20 giây)
  - **Post-cache**: Sau khi LLM + tools thực thi (TTL = 15 phút)
- Tìm kiếm câu trả lời tương tự dựa trên embedding similarity

**Luồng hoạt động**:
```
User Query
  → AnswerCache.get(query, namespace="pre-cache")
    ├─> HIT: Return cached answer (skip LLM call)
    └─> MISS: Continue to LLM
         → LLM generates answer
         → AnswerCache.set(query, answer, namespace="pre-cache" or "post-cache")
```

**Sử dụng**:
- ✅ **Đang được sử dụng** trong `RAGUseCase`
- ✅ Inject vào `rag_use_case` trong Container
- ✅ Thay thế `SemanticCacheRepository` (deprecated)

**Ví dụ sử dụng**:
```python
# Trong RAGUseCase
cached_answer = await self.answer_cache.get(query, namespace="pre-cache")
if cached_answer:
    return cached_answer  # Skip LLM call

# After LLM generation
await self.answer_cache.set(query, answer, namespace="pre-cache")
```

**Kết luận**: ✅ **GIỮ LẠI** - Đang được sử dụng tích cực

---

## 3. `context_cache.py` - Retriever Result Cache

**Vị trí**: `app/src/infrastructure/redis/context_cache.py`

**Chức năng**:
- **Cache kết quả retriever (documents)** để tránh:
  - Duplicate embedding calls
  - Duplicate Milvus queries
  - Duplicate retriever execution
- Cache key bao gồm:
  - Normalized query
  - Retriever config (k, filters, collection)
  - Embedding version (để invalidate khi model thay đổi)
- TTL: Configurable (default: 1 giờ)

**Luồng hoạt động**:
```
User Query
  → ContextCache.get(query, k, collection, filters)
    ├─> HIT: Return cached documents (skip retriever/embedding/Milvus)
    └─> MISS: Continue
         → Retriever.invoke(query)
             → Embedding (via CacheBackedEmbeddings)
             → Milvus similarity search
         → ContextCache.set(query, documents, ...)
```

**Sử dụng**:
- ⚠️ **Chưa được sử dụng trực tiếp** trong codebase hiện tại
- ✅ Được sử dụng trong `CachedRetriever` (nhưng `CachedRetriever` chưa được dùng)
- ✅ Có thể tích hợp vào `SearchUseCase` hoặc `MilvusRepository` trong tương lai

**Ví dụ sử dụng** (trong CachedRetriever):
```python
# Check cache first
cached_docs = self.context_cache.get(query, k=5, collection="products")
if cached_docs:
    return cached_docs  # Skip everything

# Execute retriever
documents = self.retriever.invoke(query)

# Cache result
self.context_cache.set(query, documents, k=5, collection="products")
```

**Kết luận**: ✅ **GIỮ LẠI** - Có tiềm năng sử dụng, đã có implementation sẵn

---

## 4. `cached_embeddings.py` - Embedding Cache

**Vị trí**: `app/src/infrastructure/embeddings/cached_embeddings.py`

**Chức năng**:
- **Wraps ONNXEmbeddings với Redis-based caching**
- Sử dụng LangChain's `CacheBackedEmbeddings` và `RedisStore`
- Đảm bảo cùng một text chỉ được embed một lần (cached trong Redis)
- Cache được share across all retrievers
- Embedding versioning để tránh stale cache

**Luồng hoạt động**:
```
Text to Embed
  → CachedONNXEmbeddings.embed_query(text)
    → CacheBackedEmbeddings (checks Redis cache)
      ├─> Cache HIT: Return cached embedding
      └─> Cache MISS: Continue
           → ONNXEmbeddings.embed_query(text)
               → requests.post("/embed")
           → Cache result in Redis
```

**Sử dụng**:
- ✅ **Đang được sử dụng** trong `MilvusRepository`
- ✅ Inject vào `milvus_repository` trong Container
- ✅ LangChain Milvus wrapper gọi `cached_embeddings.embed_query()` internally

**Ví dụ sử dụng**:
```python
# Trong Container
cached_embeddings = providers.Singleton(
    CachedONNXEmbeddings,
    base_embeddings=base_embeddings,
    redis_settings=config.provided.redis,
    embedding_settings=config.provided.embedding
)

# Trong MilvusRepository
milvus_repository = providers.Singleton(
    MilvusVectorStoreRepository,
    embedding_service=cached_embeddings  # Uses cached embeddings
)
```

**Kết luận**: ✅ **GIỮ LẠI** - Đang được sử dụng tích cực, vị trí đúng (`embeddings/`)

---

## 5. `cached_retriever.py` - Cached Retriever (Optional)

**Vị trí**: `app/src/infrastructure/retrievers/cached_retriever.py`

**Chức năng**:
- **Wraps BaseRetriever với ContextCache**
- Đảm bảo context cache được check TRƯỚC khi execute retriever
- Nếu cache HIT: skip retriever, skip embedding, skip Milvus
- Nếu cache MISS: execute retriever, sau đó cache result

**Sử dụng**:
- ⚠️ **Chưa được sử dụng** trong codebase hiện tại
- ✅ Có thể tích hợp vào `SearchUseCase` hoặc tạo retriever wrapper trong tương lai
- ✅ Vị trí đúng (`retrievers/`) vì là Retriever implementation

**Kết luận**: ✅ **GIỮ LẠI** - Có tiềm năng sử dụng, đã có implementation sẵn

---

## Tổng Kết

| File | Vị trí | Đang dùng? | Chức năng chính | Kết luận |
|------|--------|------------|-----------------|----------|
| `redis_cache.py` | `redis/` | ✅ Có | Basic key-value cache | ✅ Giữ lại |
| `answer_cache.py` | `redis/` | ✅ Có | LLM response cache | ✅ Giữ lại |
| `context_cache.py` | `redis/` | ⚠️ Chưa | Retriever result cache | ✅ Giữ lại |
| `cached_embeddings.py` | `embeddings/` | ✅ Có | Embedding cache wrapper | ✅ Giữ lại |
| `cached_retriever.py` | `retrievers/` | ⚠️ Chưa | Retriever với context cache | ✅ Giữ lại |

## Kiến Trúc Cache Layers

```
Layer 1: Answer Cache (LLM responses)
  ↓
Layer 2: Context Cache (Retriever results)
  ↓
Layer 3: Embedding Cache (Embedding vectors)
  ↓
Layer 4: Basic Redis Cache (Generic key-value)
```

Mỗi layer phục vụ một mục đích cụ thể và có thể hoạt động độc lập hoặc kết hợp với nhau.

