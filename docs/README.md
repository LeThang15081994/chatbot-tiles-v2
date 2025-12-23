# Application Layer

Application layer trong Clean Architecture chứa business logic của ứng dụng. Layer này không phụ thuộc vào infrastructure hay presentation, chỉ phụ thuộc vào domain layer.

## 📁 Cấu trúc

```
application/
├── dto/                    # Data Transfer Objects
│   ├── chat_dto.py        # Chat requests/responses
│   ├── search_dto.py      # Search requests/responses
│   ├── document_dto.py    # Document operations
│   ├── product_dto.py     # Product-related DTOs
│   ├── file_upload_dto.py # File upload DTOs
│   └── health_dto.py      # Health check DTOs
│
├── interfaces/            # Repository Interfaces (Ports)
│   ├── vector_store_repository.py
│   ├── llm_repository.py
│   ├── cache_repository.py
│   ├── embedding_repository.py
│   └── health_repository.py
│
└── use_cases/             # Business Logic Use Cases
    ├── rag_use_case.py           # RAG chat functionality
    ├── search_use_case.py        # Document search
    ├── file_upload_use_case.py   # File processing
    └── health_check_use_case.py  # Health monitoring
```

## 🎯 Các thành phần

### 1. DTOs (Data Transfer Objects)

DTOs định nghĩa cấu trúc dữ liệu chuyển giữa các layers. Sử dụng Pydantic để validation.

**Chat DTOs:**
- `ChatRequestDTO`: Request cho chat
- `ChatResponseDTO`: Response từ chatbot
- `WebSocketMessageDTO`: Messages qua WebSocket
- `ChatHistoryResponseDTO`: Lịch sử chat

**Search DTOs:**
- `SearchRequestDTO`: Request tìm kiếm
- `SearchResponseDTO`: Kết quả tìm kiếm
- `SearchResultDTO`: Một kết quả tìm kiếm

**Document DTOs:**
- `DocumentDTO`: Document entity
- `DocumentCreateRequestDTO`: Tạo document
- `DocumentUpdateRequestDTO`: Update document
- `DocumentDeleteRequestDTO`: Xóa document

**Product DTOs:**
- `ProductDTO`: Product entity
- `ProductSearchRequestDTO`: Tìm kiếm product
- `ProductMetadataDTO`: Metadata của product

**File Upload DTOs:**
- `FileUploadRequestDTO`: Upload file
- `FileUploadResponseDTO`: Kết quả upload

**Health DTOs:**
- `HealthCheckResponseDTO`: Kết quả health check
- `ServiceHealthDTO`: Health của một service

### 2. Interfaces (Repository Interfaces)

Interfaces định nghĩa contracts giữa application và infrastructure layer. Infrastructure layer sẽ implement các interfaces này.

**IVectorStoreRepository:**
```python
- search(query, k, collection_name, filter_expr)
- hybrid_search(query, k, collection_name, filter_expr)
- add_documents(documents, collection_name)
- update_document(document_id, document, collection_name)
- delete_documents(document_ids, collection_name)
- get_document(document_id, collection_name)
- get_collection_stats(collection_name)
- health_check()
```

**ILLMRepository:**
```python
- generate_response(messages, model, temperature, max_tokens)
- stream_response(messages, model, temperature, max_tokens)
- generate_with_tools(messages, tools, model, temperature)
- stream_with_tools(messages, tools, model, temperature)
- health_check()
- get_available_models()
```

**ICacheRepository:**
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

**ISemanticCacheRepository (extends ICacheRepository):**
```python
- get_similar(query, threshold)
- set_with_embedding(query, value, embedding, ttl)
```

**IEmbeddingRepository:**
```python
- embed_text(text)
- embed_texts(texts, batch_size)
- get_dimension()
- get_model_name()
- health_check()
- get_model_info()
```

**IHealthRepository:**
```python
- check_database_health()
- check_redis_health()
- check_milvus_health()
- check_llm_health()
- check_embedding_health()
- get_system_metrics()
```

### 3. Use Cases (Business Logic)

Use cases orchestrate business logic bằng cách sử dụng repositories và domain services.

**RAGUseCase:**
- `process_chat(request)`: Xử lý chat request (non-streaming)
- `stream_chat(request)`: Xử lý chat với streaming
- `get_chat_history(session_id, limit)`: Lấy lịch sử chat

**SearchUseCase:**
- `search_documents(request)`: Tìm kiếm documents
- `vector_search(query, k, collection_name)`: Vector search only
- `hybrid_search(query, k, collection_name, filter_expr)`: Hybrid search

**FileUploadUseCase:**
- `upload_and_process_file(request)`: Upload và xử lý file

**HealthCheckUseCase:**
- `check_health()`: Kiểm tra health tổng thể
- `check_readiness()`: Kiểm tra readiness
- `check_liveness()`: Kiểm tra liveness

## 🔄 Dependency Flow

```
Presentation Layer (Controllers)
    ↓
Application Layer (Use Cases)
    ↓
Domain Layer (Services)
    ↑
Infrastructure Layer (Implementations)
```

### Ví dụ Flow:

1. **Controller** nhận HTTP request
2. **Controller** chuyển đổi sang DTO
3. **Controller** gọi **Use Case** với DTO
4. **Use Case** gọi **Repository Interface** (không biết implementation)
5. **Infrastructure** implement interface và thực thi
6. Kết quả trả về qua chain ngược lại

## 💡 Nguyên tắc sử dụng

### 1. Dependency Injection

Use cases nhận dependencies qua constructor:

```python
class RAGUseCase:
    def __init__(
        self,
        vector_store: IVectorStoreRepository,  # Interface, not implementation
        llm_service: ILLMRepository,
        cache_service: Optional[ISemanticCacheRepository] = None
    ):
        self.vector_store = vector_store
        self.llm_service = llm_service
        self.cache_service = cache_service
```

### 2. Use Cases không biết Implementation

Use cases chỉ biết interfaces, không biết infrastructure implementations:

```python
# ✅ Đúng - Use interface
async def process_chat(self, request: ChatRequestDTO):
    results = await self.vector_store.hybrid_search(...)  # Interface method

# ❌ Sai - Không import infrastructure
from infrastructure.milvus.milvus_vector_store import MilvusVectorStore
```

### 3. DTOs cho Data Transfer

Luôn sử dụng DTOs để transfer data:

```python
# ✅ Đúng - Use DTO
async def process_chat(self, request: ChatRequestDTO) -> ChatResponseDTO:
    ...

# ❌ Sai - Use raw dict
async def process_chat(self, request: dict) -> dict:
    ...
```

### 4. Business Logic trong Use Cases

Use cases chứa business logic, không để trong controllers:

```python
# ✅ Đúng - Business logic in use case
class RAGUseCase:
    async def process_chat(self, request: ChatRequestDTO):
        # Check cache
        if self.cache_service:
            cached = await self.cache_service.get_similar(...)
            if cached:
                return cached

        # Retrieve documents
        docs = await self.vector_store.hybrid_search(...)

        # Build context
        context = self._build_context(docs)

        # Generate response
        answer = await self.llm_service.generate_response(...)

        return ChatResponseDTO(...)
```

## 🧪 Testing

Application layer dễ test vì sử dụng interfaces:

```python
# Mock repositories
mock_vector_store = Mock(spec=IVectorStoreRepository)
mock_llm = Mock(spec=ILLMRepository)

# Create use case with mocks
use_case = RAGUseCase(
    vector_store=mock_vector_store,
    llm_service=mock_llm
)

# Test
result = await use_case.process_chat(request)
assert result.answer == expected_answer
```

## 📚 Tài liệu tham khảo

- Clean Architecture by Robert C. Martin
- Hexagonal Architecture (Ports & Adapters)
- Use Case Driven approach
- Dependency Inversion Principle (SOLID)

