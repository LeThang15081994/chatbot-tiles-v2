# Cache Files Moved to Redis Folder

## Summary

Đã di chuyển 2 file cache về thư mục `redis/` để tập trung quản lý tất cả Redis-related code:

1. `cached_embeddings.py` - Từ `embeddings/` → `redis/`
2. `cached_retriever.py` - Từ `retrievers/` → `redis/`

## Lý Do Di Chuyển

### 1. `cached_embeddings.py`
- **Vị trí cũ**: `app/src/infrastructure/embeddings/cached_embeddings.py`
- **Vị trí mới**: `app/src/infrastructure/redis/cached_embeddings.py`
- **Lý do**:
  - Sử dụng Redis (`RedisStore`) để cache embeddings
  - Tất cả Redis-related code nên ở cùng một nơi
  - Dễ quản lý và maintain

### 2. `cached_retriever.py`
- **Vị trí cũ**: `app/src/infrastructure/retrievers/cached_retriever.py`
- **Vị trí mới**: `app/src/infrastructure/redis/cached_retriever.py`
- **Lý do**:
  - Sử dụng `ContextCache` (Redis-based) để cache retriever results
  - Phụ thuộc vào Redis, nên nên ở cùng folder với các cache khác
  - Tập trung tất cả Redis cache logic

## Cấu Trúc Mới

```
app/src/infrastructure/redis/
├── __init__.py              # Exports: AnswerCache, ContextCache, CachedONNXEmbeddings, CachedRetriever
├── answer_cache.py          # LLM response cache
├── context_cache.py         # Retriever result cache
├── cached_embeddings.py     # Embedding cache wrapper (moved from embeddings/)
└── cached_retriever.py      # Retriever with context cache (moved from retrievers/)
```

## Changes Made

### 1. `app/src/infrastructure/redis/__init__.py`
**Added exports**:
```python
from .cached_embeddings import CachedONNXEmbeddings
from .cached_retriever import CachedRetriever

__all__ = [
    "AnswerCache",
    "ContextCache",
    "CachedONNXEmbeddings",  # NEW
    "CachedRetriever",  # NEW
]
```

### 2. `app/src/infrastructure/embeddings/__init__.py`
**Removed export**:
```python
# Before
from app.src.infrastructure.embeddings.cached_embeddings import CachedONNXEmbeddings
__all__ = [..., "CachedONNXEmbeddings", ...]

# After
# Note: CachedONNXEmbeddings moved to redis/ folder
__all__ = ["ONNXEmbeddings", "TritonEmbeddingService"]
```

### 3. `app/src/bootstrap/container.py`
**Updated import**:
```python
# Before
from app.src.infrastructure.embeddings import ONNXEmbeddings, CachedONNXEmbeddings

# After
from app.src.infrastructure.embeddings import ONNXEmbeddings
from app.src.infrastructure.redis import CachedONNXEmbeddings  # Moved to redis/
```

### 4. Files Deleted
- ✅ `app/src/infrastructure/embeddings/cached_embeddings.py` (moved to `redis/`)
- ✅ `app/src/infrastructure/retrievers/cached_retriever.py` (moved to `redis/`)

## Benefits

1. ✅ **Centralized Redis Code**: Tất cả Redis-related code ở một nơi
2. ✅ **Easier Management**: Dễ tìm và quản lý các cache implementations
3. ✅ **Clear Dependencies**: Rõ ràng rằng các file này phụ thuộc vào Redis
4. ✅ **Consistent Structure**: Tuân theo nguyên tắc implementation-specific folders

## Migration Guide

Nếu có code import từ vị trí cũ:

**Before**:
```python
from app.src.infrastructure.embeddings import CachedONNXEmbeddings
from app.src.infrastructure.retrievers import CachedRetriever
```

**After**:
```python
from app.src.infrastructure.redis import CachedONNXEmbeddings, CachedRetriever
```

Hoặc:
```python
from app.src.infrastructure.redis.cached_embeddings import CachedONNXEmbeddings
from app.src.infrastructure.redis.cached_retriever import CachedRetriever
```

## Current Redis Folder Structure

Sau khi di chuyển, `redis/` folder chứa tất cả Redis-related cache implementations:

1. **`answer_cache.py`** - LLM response cache với semantic similarity
2. **`context_cache.py`** - Retriever result cache
3. **`cached_embeddings.py`** - Embedding cache wrapper (moved)
4. **`cached_retriever.py`** - Retriever với context cache (moved)

Tất cả đều phụ thuộc vào Redis và được quản lý tập trung.

