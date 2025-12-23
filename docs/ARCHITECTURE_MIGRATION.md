# Phân tích và Migration: chatbot-ceramic-tiles → Clean Architecture

## 📊 So sánh cấu trúc hiện tại vs Clean Architecture

### Cấu trúc hiện tại (chatbot-ceramic-tiles)
```
chatbot-ceramic-tiles/chat-backend/src/
├── main.py                          # ❌ Entry point, khởi tạo services trực tiếp
├── api/                             # ⚠️ Presentation layer (chưa đúng CA)
│   ├── routers/                     # ✅ Routers (đúng)
│   └── dependencies/                # ⚠️ Dependencies (nên là controllers)
├── services/                        # ❌ Lẫn lộn Application và Domain
│   ├── application/rag.py           # ⚠️ Application service (có business logic)
│   ├── domain/                      # ⚠️ Domain services (đúng vị trí nhưng sai tên)
│   └── system/                      # ⚠️ System services
├── infrastructure/                  # ✅ Infrastructure (đúng)
│   ├── embeddings/
│   ├── vector_store/
│   └── schemas/                     # ⚠️ Nên là DTOs trong application
├── core/                            # ⚠️ Core config (nên là infrastructure/config)
│   ├── settings.py
│   └── logging_config.py
├── cache/                           # ⚠️ Cache (nên là infrastructure/redis)
└── utils/                           # ⚠️ Utils (nên phân bổ vào các layer)
```

### Cấu trúc Clean Architecture (chatbot-tiles-v2)
```
src/
├── bootstrap/                       # ✅ DI Container & App initialization
│   └── main.py
├── presentation/                    # ✅ Presentation Layer
│   ├── http/
│   │   ├── controllers/            # ✅ Controllers (thay cho dependencies)
│   │   └── router/                 # ✅ Routers
│   └── sse/                        # ✅ SSE handlers
├── application/                     # ✅ Application Layer
│   ├── use_cases/                  # ✅ Use Cases (business logic)
│   ├── dto/                        # ✅ Data Transfer Objects
│   └── interfaces/                 # ✅ Repository interfaces
├── domain/                          # ✅ Domain Layer
│   ├── entities/                   # ✅ Domain entities
│   ├── services/                   # ✅ Domain services
│   └── value_objects/             # ✅ Value objects
└── infrastructure/                  # ✅ Infrastructure Layer
    ├── config/                     # ✅ Configuration
    ├── milvus/                     # ✅ Milvus implementation
    ├── postgresql/                 # ✅ PostgreSQL implementation
    └── redis/                      # ✅ Redis/Cache implementation
```

---

## 🔄 Mapping chi tiết: File cũ → Vị trí mới trong CA

### 1. **Bootstrap Layer** (`src/bootstrap/`)

| File hiện tại | Vị trí mới | Ghi chú |
|--------------|-----------|---------|
| `src/main.py` | `src/bootstrap/main.py` | ✅ Đúng vị trí, cần refactor để dùng DI container |
| - | `src/bootstrap/container.py` | 🆕 Tạo mới: DI Container (dependency injection) |
| - | `src/bootstrap/dependencies.py` | 🆕 Tạo mới: Định nghĩa dependencies |

**Cần làm:**
- Tạo DI container (ví dụ: `dependency_injector` hoặc tự implement)
- Di chuyển logic khởi tạo services từ `main.py` vào container
- Inject dependencies thay vì khởi tạo trực tiếp

---

### 2. **Presentation Layer** (`src/presentation/`)

| File hiện tại | Vị trí mới | Ghi chú |
|--------------|-----------|---------|
| `src/api/routers/api_router.py` | `src/presentation/http/router/api_router.py` | ✅ Di chuyển, giữ nguyên logic |
| `src/api/routers/ws_retrieval.py` | `src/presentation/http/router/ws_retrieval.py` | ✅ Di chuyển |
| `src/api/routers/file_upload.py` | `src/presentation/http/router/file_upload.py` | ✅ Di chuyển |
| `src/api/routers/health_router.py` | `src/presentation/http/router/health_router.py` | ✅ Di chuyển |
| `src/api/dependencies/rag.py` | `src/presentation/http/controllers/rag_controller.py` | ⚠️ Refactor: dependencies → controllers |
| `src/api/dependencies/health.py` | `src/presentation/http/controllers/health_controller.py` | ⚠️ Refactor |
| `src/api/dependencies/guardrails.py` | `src/presentation/http/controllers/guardrails_controller.py` | ⚠️ Refactor |
| - | `src/presentation/sse/` | 🆕 Tạo mới nếu cần SSE |

**Cần làm:**
- Di chuyển routers vào `presentation/http/router/`
- Chuyển dependencies thành controllers trong `presentation/http/controllers/`
- Controllers chỉ gọi use cases, không có business logic

---

### 3. **Application Layer** (`src/application/`)

| File hiện tại | Vị trí mới | Ghi chú |
|--------------|-----------|---------|
| `src/services/application/rag.py` | `src/application/use_cases/rag_use_case.py` | ⚠️ Refactor: tách business logic |
| `src/services/application/rag.py` (SearchArgs) | `src/application/dto/search_dto.py` | ⚠️ Tách DTOs |
| `src/infrastructure/schemas/request.py` | `src/application/dto/request_dto.py` | ✅ Di chuyển |
| `src/infrastructure/schemas/response.py` | `src/application/dto/response_dto.py` | ✅ Di chuyển |
| - | `src/application/interfaces/vector_store_repository.py` | 🆕 Tạo mới: Interface cho vector store |
| - | `src/application/interfaces/llm_repository.py` | 🆕 Tạo mới: Interface cho LLM |
| - | `src/application/interfaces/cache_repository.py` | 🆕 Tạo mới: Interface cho cache |

**Cần làm:**
- Tách business logic từ `rag.py` thành use cases
- Tạo DTOs cho request/response
- Tạo interfaces (abstractions) cho repositories
- Use cases chỉ gọi domain services và repositories qua interfaces

---

### 4. **Domain Layer** (`src/domain/`)

| File hiện tại | Vị trí mới | Ghi chú |
|--------------|-----------|---------|
| `src/services/domain/websocket.py` | `src/domain/services/websocket_service.py` | ✅ Di chuyển, giữ nguyên |
| `src/services/domain/summarize.py` | `src/domain/services/summarize_service.py` | ✅ Di chuyển |
| `src/services/domain/base.py` | `src/domain/services/base_service.py` | ✅ Di chuyển |
| - | `src/domain/entities/chat_message.py` | 🆕 Tạo mới: Chat message entity |
| - | `src/domain/entities/document.py` | 🆕 Tạo mới: Document entity |
| - | `src/domain/value_objects/search_query.py` | 🆕 Tạo mới: Value object cho search |
| `src/utils/text_processing.py` | `src/domain/services/text_processing_service.py` | ⚠️ Di chuyển nếu là domain logic |

**Cần làm:**
- Di chuyển domain services
- Tạo entities cho domain objects
- Tạo value objects cho immutable data
- Domain layer không phụ thuộc vào infrastructure

---

### 5. **Infrastructure Layer** (`src/infrastructure/`)

| File hiện tại | Vị trí mới | Ghi chú |
|--------------|-----------|---------|
| `src/core/settings.py` | `src/infrastructure/config/settings.py` | ✅ Di chuyển |
| `src/core/logging_config.py` | `src/infrastructure/config/logging_config.py` | ✅ Di chuyển |
| `src/infrastructure/vector_store/milvus_vector_stores.py` | `src/infrastructure/milvus/milvus_vector_store.py` | ✅ Di chuyển, implement interface |
| `src/infrastructure/embeddings/embedding.py` | `src/infrastructure/milvus/embedding_service.py` | ✅ Di chuyển |
| `src/cache/semantic_cache.py` | `src/infrastructure/redis/semantic_cache.py` | ✅ Di chuyển |
| `src/cache/standard_cache.py` | `src/infrastructure/redis/standard_cache.py` | ✅ Di chuyển |
| - | `src/infrastructure/postgresql/` | 🆕 Tạo mới nếu cần PostgreSQL repository |
| - | `src/infrastructure/redis/redis_client.py` | 🆕 Tạo mới: Redis client wrapper |

**Cần làm:**
- Di chuyển tất cả infrastructure code
- Implement các interfaces từ application layer
- Tách biệt implementation details

---

## 🎯 Nguyên tắc Clean Architecture cần tuân thủ

### 1. **Dependency Rule**
- ✅ Inner layers không phụ thuộc outer layers
- ✅ Domain layer độc lập hoàn toàn
- ✅ Application layer chỉ phụ thuộc Domain
- ✅ Infrastructure implement interfaces từ Application

### 2. **Dependency Injection (DI)**
- ✅ Tất cả dependencies được inject qua constructor
- ✅ Sử dụng DI container để quản lý dependencies
- ✅ Không khởi tạo services trực tiếp trong code

### 3. **Separation of Concerns**
- ✅ Controllers chỉ xử lý HTTP requests/responses
- ✅ Use cases chứa business logic
- ✅ Domain services chứa domain logic
- ✅ Infrastructure chỉ implement technical details

---

## 📝 Checklist Migration

### Phase 1: Setup Infrastructure
- [ ] Tạo cấu trúc thư mục mới theo CA
- [ ] Setup DI container (dependency_injector hoặc tự implement)
- [ ] Di chuyển config files vào `infrastructure/config/`

### Phase 2: Domain Layer
- [ ] Di chuyển domain services
- [ ] Tạo entities và value objects
- [ ] Đảm bảo domain layer không có dependencies

### Phase 3: Application Layer
- [ ] Tạo interfaces (repositories)
- [ ] Tạo DTOs
- [ ] Refactor business logic thành use cases
- [ ] Use cases gọi domain services và repositories

### Phase 4: Infrastructure Layer
- [ ] Di chuyển tất cả infrastructure code
- [ ] Implement interfaces từ application layer
- [ ] Setup Redis, Milvus implementations

### Phase 5: Presentation Layer
- [ ] Di chuyển routers
- [ ] Chuyển dependencies thành controllers
- [ ] Controllers gọi use cases qua DI

### Phase 6: Bootstrap
- [ ] Setup DI container
- [ ] Đăng ký tất cả dependencies
- [ ] Refactor main.py để dùng DI

---

## 🔧 Ví dụ Migration

### Trước (chatbot-ceramic-tiles):
```python
# src/main.py
app.state.rag_service = Rag()  # ❌ Khởi tạo trực tiếp

# src/services/application/rag.py
class Rag:
    def __init__(self):
        self.llm = ChatOpenAI(**settings.llm_config)  # ❌ Phụ thuộc trực tiếp
        self.milvus_client = milvus_vector_store  # ❌ Global instance
```

### Sau (Clean Architecture):
```python
# src/bootstrap/container.py
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    # Infrastructure
    vector_store = providers.Singleton(
        MilvusVectorStore,
        settings=config
    )

    llm_service = providers.Singleton(
        LLMService,
        base_url=config.litellm_base_url
    )

    # Application
    rag_use_case = providers.Factory(
        RAGUseCase,
        vector_store=vector_store,
        llm_service=llm_service
    )

# src/application/use_cases/rag_use_case.py
class RAGUseCase:
    def __init__(
        self,
        vector_store: IVectorStoreRepository,  # Interface
        llm_service: ILLMRepository  # Interface
    ):
        self.vector_store = vector_store
        self.llm_service = llm_service

# src/presentation/http/controllers/rag_controller.py
class RAGController:
    def __init__(self, rag_use_case: RAGUseCase):  # Injected
        self.rag_use_case = rag_use_case
```

---

## 📚 Tài liệu tham khảo

- Clean Architecture by Robert C. Martin
- Dependency Injection patterns
- Repository pattern
- Use Case pattern

