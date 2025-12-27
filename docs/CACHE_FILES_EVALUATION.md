# Đánh Giá Vị Trí Các File Cache

## Kết Quả Đánh Giá

### 1. `cached_embeddings.py`

**Vị trí hiện tại**: `app/src/infrastructure/embeddings/cached_embeddings.py`

**Đánh giá**:
- ✅ **Vị trí ĐÚNG** - Nên giữ ở `embeddings/`
- ✅ **Lý do**: Đây là một Embeddings implementation (inherits from `Embeddings`)
- ✅ **Đang được sử dụng**: Inject vào `milvus_repository` trong Container
- ✅ **Không cần di chuyển**

**Kết luận**: ✅ **GIỮ NGUYÊN** ở `embeddings/`

---

### 2. `cached_retriever.py`

**Vị trí hiện tại**: `app/src/infrastructure/retrievers/cached_retriever.py`

**Đánh giá**:
- ✅ **Vị trí ĐÚNG** - Nên giữ ở `retrievers/`
- ✅ **Lý do**: Đây là một Retriever implementation (inherits from `BaseRetriever`)
- ⚠️ **Chưa được sử dụng**: Chưa có code nào import/use `CachedRetriever`
- ✅ **Có tiềm năng**: Có thể tích hợp vào `SearchUseCase` hoặc tạo retriever wrapper
- ✅ **Không cần di chuyển**

**Kết luận**: ✅ **GIỮ NGUYÊN** ở `retrievers/` (có thể dùng trong tương lai)

---

### 3. `redis_cache.py`

**Vị trí hiện tại**: `app/src/infrastructure/redis/redis_cache.py`

**Đánh giá**:
- ✅ **Vị trí ĐÚNG** - Nên giữ ở `redis/`
- ✅ **Đang được sử dụng**:
  - Inject vào `health_repository` trong Container
  - Sử dụng trong `HealthRepository.check_redis_health()`
- ✅ **Không nên xóa**

**Kết luận**: ✅ **GIỮ LẠI** - Vẫn được sử dụng

---

## Tổng Kết

| File | Vị trí hiện tại | Đánh giá | Hành động |
|------|----------------|----------|-----------|
| `cached_embeddings.py` | `embeddings/` | ✅ Đúng | ✅ Giữ nguyên |
| `cached_retriever.py` | `retrievers/` | ✅ Đúng | ✅ Giữ nguyên |
| `redis_cache.py` | `redis/` | ✅ Đúng, đang dùng | ✅ Giữ lại |

## Nguyên Tắc Tổ Chức

1. **Implementation-specific folders**:
   - `embeddings/` - Tất cả Embeddings implementations
   - `retrievers/` - Tất cả Retriever implementations
   - `redis/` - Tất cả Redis-related cache implementations

2. **Separation of concerns**:
   - Embeddings logic → `embeddings/`
   - Retriever logic → `retrievers/`
   - Cache logic (Redis-specific) → `redis/`

3. **Consistency**:
   - Các file cùng loại ở cùng folder
   - Dễ tìm và quản lý

## Kết Luận

**KHÔNG CẦN DI CHUYỂN** bất kỳ file nào. Tất cả đã ở đúng vị trí theo nguyên tắc:
- `cached_embeddings.py` → `embeddings/` (Embeddings implementation)
- `cached_retriever.py` → `retrievers/` (Retriever implementation)
- `redis_cache.py` → `redis/` (Redis cache implementation)

Cấu trúc hiện tại đã hợp lý và tuân theo best practices.

