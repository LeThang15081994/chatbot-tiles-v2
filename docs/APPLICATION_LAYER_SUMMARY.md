# Application Layer - Tóm tắt

## ✅ Đã hoàn thành

Đã tạo **19 files** cho Application Layer theo Clean Architecture:

### 📦 DTOs (Data Transfer Objects) - 7 files

```
src/application/dto/
├── __init__.py                  # Exports tất cả DTOs
├── chat_dto.py                  # Chat requests/responses, WebSocket messages
├── search_dto.py                # Search requests/responses, filters
├── document_dto.py              # Document operations (CRUD)
├── product_dto.py               # Product-related DTOs
├── file_upload_dto.py           # File upload requests/responses
└── health_dto.py                # Health check responses
```

**Tổng cộng: 40+ DTOs** bao gồm:
- ChatRequestDTO, ChatResponseDTO, WebSocketMessageDTO
- SearchRequestDTO, SearchResponseDTO, SearchResultDTO
- DocumentDTO, ProductDTO
- FileUploadRequestDTO, FileUploadResponseDTO
- HealthCheckResponseDTO, ServiceHealthDTO

### 🔌 Interfaces (Repository Interfaces) - 6 files

```
src/application/interfaces/
├── __init__.py                         # Exports tất cả interfaces
├── vector_store_repository.py          # 11 methods
├── llm_repository.py                   # 7 methods
├── cache_repository.py                 # 10 methods (bao gồm semantic cache)
├── embedding_repository.py             # 7 methods
└── health_repository.py                # 6 methods
```

**Tổng cộng: 41 abstract methods** định nghĩa contracts với infrastructure.

### 🎯 Use Cases (Business Logic) - 5 files

```
src/application/use_cases/
├── __init__.py                  # Exports tất cả use cases
├── rag_use_case.py             # RAG chat (streaming & non-streaming)
├── search_use_case.py          # Document search (vector, BM25, hybrid)
├── file_upload_use_case.py     # File processing và embedding
└── health_check_use_case.py    # Health monitoring
```

**Tổng cộng: 15+ public methods** cho business logic.

### 📚 Documentation - 1 file

```
src/application/README.md        # Comprehensive documentation
```

---

## 📊 Chi tiết từng component

### 1. DTOs (Data Transfer Objects)

#### Chat DTOs
- `ChatRequestDTO`: User question, session_id, user_id, stream flag
- `ChatResponseDTO`: Answer, sources, products, processing time
- `ChatMessageDTO`: Single message (role, content)
- `WebSocketMessageDTO`: Streaming messages (type, data, metadata)
- `ChatHistoryResponseDTO`: Chat history với messages

#### Search DTOs
- `SearchRequestDTO`: Query, top_k, collection_name, metadata_filter
- `SearchResponseDTO`: Results, query, collection, total_results
- `SearchResultDTO`: Content, metadata, score
- `SearchMetadataDTO`: id, category, source, brand, scores

#### Document DTOs
- `DocumentDTO`: id, content, metadata, vector
- `DocumentMetadataDTO`: source, category, brand, timestamps
- `DocumentCreateRequestDTO`: Tạo document mới
- `DocumentUpdateRequestDTO`: Update document
- `DocumentDeleteRequestDTO`: Xóa documents
- `DocumentOperationResponseDTO`: Kết quả operations

#### Product DTOs
- `ProductDTO`: Full product info với metadata
- `ProductMetadataDTO`: Product metadata only
- `ProductSearchRequestDTO`: Search products với filters
- `ProductSearchResponseDTO`: Product search results

#### File Upload DTOs
- `FileUploadRequestDTO`: filename, file_content, file_type, size, extension
- `FileUploadResponseDTO`: success, file_id, documents_created, processing_time

#### Health DTOs
- `HealthCheckResponseDTO`: Overall health với tất cả services
- `ServiceHealthDTO`: Individual service health
- `ReadinessCheckResponseDTO`: Readiness check
- `HealthStatus` enum: HEALTHY, UNHEALTHY, DEGRADED

---

### 2. Interfaces (Repository Interfaces)

#### IVectorStoreRepository (11 methods)
```python
- search(query, k, collection_name, filter_expr)
- hybrid_search(query, k, collection_name, filter_expr)
- add_documents(documents, collection_name)
- update_document(document_id, document, collection_name)
- delete_documents(document_ids, collection_name)
- get_document(document_id, collection_name)
- get_collection_stats(collection_name)
- list_collections()
- health_check()
```

#### ILLMRepository (7 methods)
```python
- generate_response(messages, model, temperature, max_tokens)
- stream_response(messages, model, temperature, max_tokens)
- generate_with_tools(messages, tools, model, temperature)
- stream_with_tools(messages, tools, model, temperature)
- health_check()
- get_available_models()
```

#### ICacheRepository (8 methods)
```python
- get(key)
- set(key, value, ttl)
- delete(key)
- exists(key)
- clear(pattern)
- get_ttl(key)
- health_check()
- get_stats()
```

#### ISemanticCacheRepository (extends ICacheRepository, +2 methods)
```python
- get_similar(query, threshold)
- set_with_embedding(query, value, embedding, ttl)
```

#### IEmbeddingRepository (7 methods)
```python
- embed_text(text)
- embed_texts(texts, batch_size)
- get_dimension()
- get_model_name()
- health_check()
- get_model_info()
- get_cache_info()
```

#### IHealthRepository (6 methods)
```python
- check_database_health()
- check_redis_health()
- check_milvus_health()
- check_llm_health()
- check_embedding_health()
- get_system_metrics()
```

---

### 3. Use Cases (Business Logic)

#### RAGUseCase
```python
class RAGUseCase:
    def __init__(
        self,
        vector_store: IVectorStoreRepository,
        llm_service: ILLMRepository,
        cache_service: Optional[ISemanticCacheRepository] = None
    )

    # Public methods:
    - process_chat(request: ChatRequestDTO) -> ChatResponseDTO
    - stream_chat(request: ChatRequestDTO) -> AsyncGenerator[WebSocketMessageDTO]
    - get_chat_history(session_id, limit) -> ChatHistoryResponseDTO

    # Private helpers:
    - _build_context(search_results)
    - _prepare_messages(question, context, session_id)
```

#### SearchUseCase
```python
class SearchUseCase:
    def __init__(self, vector_store: IVectorStoreRepository)

    # Public methods:
    - search_documents(request: SearchRequestDTO) -> SearchResponseDTO
    - vector_search(query, k, collection_name) -> List[SearchResultDTO]
    - hybrid_search(query, k, collection_name, filter_expr) -> List[SearchResultDTO]

    # Private helpers:
    - _determine_collection(collection_type, query)
    - _build_filter_expression(metadata_filter, collection_name)
```

#### FileUploadUseCase
```python
class FileUploadUseCase:
    def __init__(
        self,
        vector_store: IVectorStoreRepository,
        embedding_service: IEmbeddingRepository
    )

    # Public methods:
    - upload_and_process_file(request: FileUploadRequestDTO) -> FileUploadResponseDTO

    # Private helpers:
    - _extract_text_from_file(file_content, file_extension)
    - _chunk_text(text, chunk_size, chunk_overlap)
```

#### HealthCheckUseCase
```python
class HealthCheckUseCase:
    def __init__(
        self,
        health_repository: IHealthRepository,
        service_name: str,
        version: str
    )

    # Public methods:
    - check_health() -> HealthCheckResponseDTO
    - check_readiness() -> ReadinessCheckResponseDTO
    - check_liveness() -> bool

    # Private helpers:
    - _determine_overall_status(services)
```

---

## 🎯 Cách sử dụng

### 1. Import DTOs

```python
from src.application.dto import (
    ChatRequestDTO,
    ChatResponseDTO,
    SearchRequestDTO,
    SearchResponseDTO,
)
```

### 2. Import Interfaces

```python
from src.application.interfaces import (
    IVectorStoreRepository,
    ILLMRepository,
    ICacheRepository,
)
```

### 3. Import Use Cases

```python
from src.application.use_cases import (
    RAGUseCase,
    SearchUseCase,
    HealthCheckUseCase,
)
```

### 4. Sử dụng với Dependency Injection

```python
# Infrastructure implementations
from infrastructure.milvus import MilvusVectorStore
from infrastructure.llm import LiteLLMClient
from infrastructure.redis import SemanticCache

# Instantiate implementations
vector_store = MilvusVectorStore(settings)
llm_service = LiteLLMClient(settings)
cache_service = SemanticCache(settings)

# Inject vào use case
rag_use_case = RAGUseCase(
    vector_store=vector_store,    # IVectorStoreRepository
    llm_service=llm_service,      # ILLMRepository
    cache_service=cache_service   # ISemanticCacheRepository
)

# Sử dụng use case
request = ChatRequestDTO(
    question="Gạch wooden là gì?",
    session_id="session_123"
)
response = await rag_use_case.process_chat(request)
```

---

## ✅ Checklist tiếp theo

### Phase 1: Infrastructure Implementation
- [ ] Implement `IVectorStoreRepository` → `MilvusVectorStore`
- [ ] Implement `ILLMRepository` → `LiteLLMClient`
- [ ] Implement `ICacheRepository` → `RedisCache`
- [ ] Implement `ISemanticCacheRepository` → `SemanticCache`
- [ ] Implement `IEmbeddingRepository` → `EmbeddingService`
- [ ] Implement `IHealthRepository` → `HealthService`

### Phase 2: Presentation Layer
- [ ] Create Controllers sử dụng Use Cases
- [ ] Create Routers
- [ ] Setup FastAPI dependencies

### Phase 3: Bootstrap & DI
- [ ] Setup DI Container (dependency_injector hoặc tự implement)
- [ ] Register tất cả dependencies
- [ ] Refactor main.py để sử dụng DI

### Phase 4: Testing
- [ ] Unit tests cho Use Cases (với mocked repositories)
- [ ] Integration tests
- [ ] End-to-end tests

---

## 📝 Lưu ý quan trọng

1. **DTOs are immutable**: Sử dụng Pydantic BaseModel, không modify sau khi tạo
2. **Interfaces define contracts**: Infrastructure PHẢI implement tất cả methods
3. **Use Cases contain business logic**: Không để business logic trong controllers
4. **Dependency Injection**: LUÔN inject dependencies qua constructor
5. **No infrastructure imports in application**: Application chỉ biết interfaces

---

## 🎉 Tổng kết

✅ **19 files** đã được tạo
✅ **40+ DTOs** cho data transfer
✅ **5 interfaces** với **41 abstract methods**
✅ **4 use cases** với **15+ public methods**
✅ **1 comprehensive README**

Application Layer hoàn chỉnh và tuân thủ Clean Architecture principles!

