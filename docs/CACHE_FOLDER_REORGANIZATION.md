# Cache Folder Reorganization

## Summary

All cache implementations have been moved to `app/src/infrastructure/redis/` folder for better organization and management.

## Rationale

### Why `redis/` instead of `cache/`?

1. **Implementation-Specific**: All cache implementations use Redis as the backend
   - `AnswerCache`: Uses `RedisSemanticCache` (Redis-based)
   - `ContextCache`: Uses `redis.Redis` client directly
   - `RedisCacheRepository`: Basic Redis cache

2. **Consistency**: All Redis-related code is now in one place
   - Easier to manage and maintain
   - Clear separation: Redis-specific code vs. generic cache interfaces

3. **Future-Proofing**: If we need to add other cache backends (e.g., Memcached), we can create separate folders:
   - `app/src/infrastructure/redis/` - Redis implementations
   - `app/src/infrastructure/memcached/` - Memcached implementations (if needed)

## Changes Made

### Files Moved

1. **`app/src/infrastructure/cache/answer_cache.py`**
   - **From**: `app/src/infrastructure/cache/answer_cache.py`
   - **To**: `app/src/infrastructure/redis/answer_cache.py`
   - **Reason**: Uses `RedisSemanticCache` (Redis-specific)

2. **`app/src/infrastructure/cache/context_cache.py`**
   - **From**: `app/src/infrastructure/cache/context_cache.py`
   - **To**: `app/src/infrastructure/redis/context_cache.py`
   - **Reason**: Uses `redis.Redis` client directly (Redis-specific)

### Files Updated

1. **`app/src/infrastructure/redis/__init__.py`**
   - Added exports for `AnswerCache` and `ContextCache`
   - Updated documentation

2. **`app/src/bootstrap/container.py`**
   - Changed imports from:
     ```python
     from app.src.infrastructure.cache.context_cache import ContextCache
     from app.src.infrastructure.cache.answer_cache import AnswerCache
     ```
   - To:
     ```python
     from app.src.infrastructure.redis import ContextCache, AnswerCache
     ```

3. **`app/src/infrastructure/retrievers/cached_retriever.py`**
   - Changed import from:
     ```python
     from app.src.infrastructure.cache.context_cache import ContextCache
     ```
   - To:
     ```python
     from app.src.infrastructure.redis import ContextCache
     ```

### Files Deleted

1. `app/src/infrastructure/cache/answer_cache.py` (moved to `redis/`)
2. `app/src/infrastructure/cache/context_cache.py` (moved to `redis/`)

**Note**: The `cache/` folder is now empty and can be removed if desired.

## New Folder Structure

```
app/src/infrastructure/redis/
├── __init__.py              # Exports all Redis cache implementations
├── redis_cache.py           # Basic Redis cache (key-value)
├── answer_cache.py          # LLM response cache (moved from cache/)
├── context_cache.py         # Retriever result cache (moved from cache/)
└── semantic_cache.py        # Deprecated (replaced by AnswerCache + ContextCache)
```

## Benefits

1. **Better Organization**: All Redis-related code in one place
2. **Easier Maintenance**: Clear where to find Redis cache implementations
3. **Consistent Structure**: Follows the pattern of implementation-specific folders
4. **Clear Dependencies**: Makes it obvious that these caches depend on Redis

## Migration Guide

If you have code that imports from the old location:

**Before**:
```python
from app.src.infrastructure.cache.answer_cache import AnswerCache
from app.src.infrastructure.cache.context_cache import ContextCache
```

**After**:
```python
from app.src.infrastructure.redis import AnswerCache, ContextCache
```

Or use the full path:
```python
from app.src.infrastructure.redis.answer_cache import AnswerCache
from app.src.infrastructure.redis.context_cache import ContextCache
```

## Testing

After this reorganization:
- ✅ All imports updated
- ✅ No broken references
- ✅ Linter warnings are only for missing packages (not code issues)
- ✅ Folder structure is cleaner and more logical

