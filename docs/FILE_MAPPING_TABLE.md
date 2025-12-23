# Bảng Mapping Chi Tiết: chatbot-ceramic-tiles → Clean Architecture

## 📋 Bảng Mapping Đầy Đủ

| File/Directory Hiện Tại | Vị trí Mới trong CA | Loại | Ghi chú |
|------------------------|---------------------|------|---------|
| **BOOTSTRAP LAYER** |
| `src/main.py` | `src/bootstrap/main.py` | ✅ Di chuyển | Refactor để dùng DI container |
| - | `src/bootstrap/container.py` | 🆕 Tạo mới | DI Container setup |
| - | `src/bootstrap/dependencies.py` | 🆕 Tạo mới | Dependency definitions |
| **PRESENTATION LAYER** |
| `src/api/routers/api_router.py` | `src/presentation/http/router/api_router.py` | ✅ Di chuyển | Giữ nguyên logic |
| `src/api/routers/ws_retrieval.py` | `src/presentation/http/router/ws_retrieval.py` | ✅ Di chuyển | WebSocket router |
| `src/api/routers/file_upload.py` | `src/presentation/http/router/file_upload.py` | ✅ Di chuyển | File upload router |
| `src/api/routers/health_router.py` | `src/presentation/http/router/health_router.py` | ✅ Di chuyển | Health check router |
| `src/api/dependencies/rag.py` | `src/presentation/http/controllers/rag_controller.py` | ⚠️ Refactor | Chuyển thành controller |
| `src/api/dependencies/health.py` | `src/presentation/http/controllers/health_controller.py` | ⚠️ Refactor | Chuyển thành controller |
| `src/api/dependencies/guardrails.py` | `src/presentation/http/controllers/guardrails_controller.py` | ⚠️ Refactor | Chuyển thành controller |
| - | `src/presentation/sse/` | 🆕 Tạo mới | Nếu cần SSE handlers |
| **APPLICATION LAYER** |
| `src/services/application/rag.py` | `src/application/use_cases/rag_use_case.py` | ⚠️ Refactor | Tách business logic |
| `src/services/application/rag.py` (SearchArgs) | `src/application/dto/search_dto.py` | ⚠️ Tách | Tách DTOs |
| `src/infrastructure/schemas/request.py` | `src/application/dto/request_dto.py` | ✅ Di chuyển | Request DTOs |
| `src/infrastructure/schemas/response.py` | `src/application/dto/response_dto.py` | ✅ Di chuyển | Response DTOs |
| - | `src/application/interfaces/vector_store_repository.py` | 🆕 Tạo mới | Interface cho vector store |
| - | `src/application/interfaces/llm_repository.py` | 🆕 Tạo mới | Interface cho LLM |
| - | `src/application/interfaces/cache_repository.py` | 🆕 Tạo mới | Interface cho cache |
| - | `src/application/interfaces/embedding_repository.py` | 🆕 Tạo mới | Interface cho embeddings |
| **DOMAIN LAYER** |
| `src/services/domain/websocket.py` | `src/domain/services/websocket_service.py` | ✅ Di chuyển | Domain service |
| `src/services/domain/summarize.py` | `src/domain/services/summarize_service.py` | ✅ Di chuyển | Domain service |
| `src/services/domain/base.py` | `src/domain/services/base_service.py` | ✅ Di chuyển | Base domain service |
| `src/utils/text_processing.py` | `src/domain/services/text_processing_service.py` | ⚠️ Di chuyển | Nếu là domain logic |
| - | `src/domain/entities/chat_message.py` | 🆕 Tạo mới | Chat message entity |
| - | `src/domain/entities/document.py` | 🆕 Tạo mới | Document entity |
| - | `src/domain/entities/product.py` | 🆕 Tạo mới | Product entity (nếu cần) |
| - | `src/domain/value_objects/search_query.py` | 🆕 Tạo mới | Search query VO |
| - | `src/domain/value_objects/embedding.py` | 🆕 Tạo mới | Embedding VO |
| **INFRASTRUCTURE LAYER** |
| `src/core/settings.py` | `src/infrastructure/config/settings.py` | ✅ Di chuyển | Configuration |
| `src/core/logging_config.py` | `src/infrastructure/config/logging_config.py` | ✅ Di chuyển | Logging config |
| `src/core/prompts.yml` | `src/infrastructure/config/prompts.yml` | ✅ Di chuyển | Prompts config |
| `src/infrastructure/vector_store/milvus_vector_stores.py` | `src/infrastructure/milvus/milvus_vector_store.py` | ⚠️ Refactor | Implement interface |
| `src/infrastructure/embeddings/embedding.py` | `src/infrastructure/milvus/embedding_service.py` | ✅ Di chuyển | Embedding service |
| `src/cache/semantic_cache.py` | `src/infrastructure/redis/semantic_cache.py` | ✅ Di chuyển | Semantic cache |
| `src/cache/standard_cache.py` | `src/infrastructure/redis/standard_cache.py` | ✅ Di chuyển | Standard cache |
| - | `src/infrastructure/redis/redis_client.py` | 🆕 Tạo mới | Redis client wrapper |
| - | `src/infrastructure/milvus/milvus_client.py` | 🆕 Tạo mới | Milvus client wrapper |
| - | `src/infrastructure/llm/litellm_client.py` | 🆕 Tạo mới | LiteLLM client wrapper |
| - | `src/infrastructure/postgresql/postgresql_client.py` | 🆕 Tạo mới | PostgreSQL client (nếu cần) |
| **UTILITIES & OTHERS** |
| `src/utils/text_processing.py` | `src/domain/services/text_processing_service.py` | ⚠️ Di chuyển | Nếu là domain logic |
| `src/utils/text_processing.py` | `src/infrastructure/utils/text_processing.py` | ⚠️ Di chuyển | Nếu là infrastructure util |

---

## 🎯 Chi Tiết Refactoring

### 1. **RAG Service → Use Case**

**Trước:**
```python
# src/services/application/rag.py
class Rag:
    def __init__(self):
        self.llm = ChatOpenAI(**settings.llm_config)  # ❌ Direct dependency
        self.milvus_client = milvus_vector_store  # ❌ Global instance
        # ... business logic mixed with infrastructure
```

**Sau:**
```python
# src/application/use_cases/rag_use_case.py
class RAGUseCase:
    def __init__(
        self,
        vector_store: IVectorStoreRepository,
        llm_service: ILLMRepository,
        cache_service: ICacheRepository,
        summarize_service: SummarizeService
    ):
        self.vector_store = vector_store
        self.llm_service = llm_service
        self.cache_service = cache_service
        self.summarize_service = summarize_service

    async def process_chat(
        self,
        query: str,
        session_id: str
    ) -> ChatResponseDTO:
        # Pure business logic
        pass
```

### 2. **Dependencies → Controllers**

**Trước:**
```python
# src/api/dependencies/rag.py
def get_rag_service():
    return app.state.rag_service  # ❌ Global state
```

**Sau:**
```python
# src/presentation/http/controllers/rag_controller.py
class RAGController:
    def __init__(self, rag_use_case: RAGUseCase):
        self.rag_use_case = rag_use_case

    async def chat(self, request: ChatRequestDTO) -> ChatResponseDTO:
        return await self.rag_use_case.process_chat(
            query=request.query,
            session_id=request.session_id
        )
```

### 3. **Infrastructure Implementation**

**Trước:**
```python
# src/infrastructure/vector_store/milvus_vector_stores.py
class MilvusVectorStore:
    # Direct implementation
```

**Sau:**
```python
# src/application/interfaces/vector_store_repository.py
class IVectorStoreRepository(ABC):
    @abstractmethod
    async def search(self, query: str, k: int) -> List[Document]:
        pass

# src/infrastructure/milvus/milvus_vector_store.py
class MilvusVectorStore(IVectorStoreRepository):
    def __init__(self, settings: Settings):
        # Implementation
        pass

    async def search(self, query: str, k: int) -> List[Document]:
        # Implementation
        pass
```

---

## 📊 Dependency Flow

```
Presentation Layer
    ↓ (calls)
Application Layer (Use Cases)
    ↓ (uses)
Domain Layer (Services, Entities)
    ↑ (implements)
Infrastructure Layer (Repositories, Clients)
```

### Ví dụ Flow:

1. **Controller** nhận HTTP request
2. **Controller** gọi **Use Case** với DTO
3. **Use Case** gọi **Domain Service** cho business logic
4. **Use Case** gọi **Repository Interface** (không biết implementation)
5. **Infrastructure Repository** implement interface và gọi external services

---

## ✅ Checklist Migration từng File

### Phase 1: Infrastructure Config
- [ ] `src/core/settings.py` → `src/infrastructure/config/settings.py`
- [ ] `src/core/logging_config.py` → `src/infrastructure/config/logging_config.py`
- [ ] `src/core/prompts.yml` → `src/infrastructure/config/prompts.yml`

### Phase 2: Infrastructure Implementations
- [ ] `src/infrastructure/vector_store/milvus_vector_stores.py` → `src/infrastructure/milvus/milvus_vector_store.py`
- [ ] `src/infrastructure/embeddings/embedding.py` → `src/infrastructure/milvus/embedding_service.py`
- [ ] `src/cache/semantic_cache.py` → `src/infrastructure/redis/semantic_cache.py`
- [ ] `src/cache/standard_cache.py` → `src/infrastructure/redis/standard_cache.py`

### Phase 3: Domain Layer
- [ ] `src/services/domain/websocket.py` → `src/domain/services/websocket_service.py`
- [ ] `src/services/domain/summarize.py` → `src/domain/services/summarize_service.py`
- [ ] `src/services/domain/base.py` → `src/domain/services/base_service.py`
- [ ] Tạo entities và value objects

### Phase 4: Application Layer
- [ ] Tạo interfaces trong `src/application/interfaces/`
- [ ] Tạo DTOs trong `src/application/dto/`
- [ ] Refactor `src/services/application/rag.py` → `src/application/use_cases/rag_use_case.py`

### Phase 5: Presentation Layer
- [ ] `src/api/routers/*` → `src/presentation/http/router/*`
- [ ] `src/api/dependencies/*` → `src/presentation/http/controllers/*`

### Phase 6: Bootstrap
- [ ] Setup DI container
- [ ] Refactor `src/main.py` → `src/bootstrap/main.py`
- [ ] Đăng ký tất cả dependencies

---

## 🔍 Lưu Ý Quan Trọng

1. **Không phá vỡ chức năng hiện tại**: Migration từng phần, test sau mỗi bước
2. **Dependency Injection**: Tất cả dependencies phải được inject, không khởi tạo trực tiếp
3. **Interfaces**: Application layer chỉ biết interfaces, không biết implementations
4. **Domain Independence**: Domain layer không được phụ thuộc vào bất kỳ layer nào khác
5. **Testing**: Dễ dàng test hơn với CA vì có thể mock interfaces

