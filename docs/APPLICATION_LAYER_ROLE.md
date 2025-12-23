# Vai trò của Application Layer trong Clean Architecture

## 🎯 TỔNG QUAN

**Application Layer** là lớp trung tâm trong Clean Architecture, chứa **business logic** và **use cases** của ứng dụng. Layer này **không phụ thuộc** vào infrastructure hay presentation, chỉ phụ thuộc vào Domain layer.

---

## 📐 VỊ TRÍ TRONG CLEAN ARCHITECTURE

```
┌─────────────────────────────────────┐
│   Presentation Layer (Controllers) │  ← HTTP/WebSocket handlers
├─────────────────────────────────────┤
│   Application Layer (Use Cases)    │  ← Business Logic ⭐
├─────────────────────────────────────┤
│   Domain Layer (Entities/Services) │  ← Core Business Rules
├─────────────────────────────────────┤
│   Infrastructure Layer              │  ← External Services (DB, APIs)
└─────────────────────────────────────┘
```

**Dependency Rule**:
- ✅ Application Layer **phụ thuộc vào** Domain Layer
- ✅ Application Layer **không phụ thuộc vào** Infrastructure Layer (dùng interfaces)
- ✅ Application Layer **không phụ thuộc vào** Presentation Layer

---

## 🏗️ CẤU TRÚC APPLICATION LAYER

### 1. **DTOs (Data Transfer Objects)** - `dto/`

**Vai trò**: Định nghĩa cấu trúc dữ liệu chuyển giữa các layers

**Files**:
- `chat_dto.py` - Chat requests/responses
- `search_dto.py` - Search requests/responses
- `document_dto.py` - Document operations
- `product_dto.py` - Product-related DTOs
- `file_upload_dto.py` - File upload DTOs
- `health_dto.py` - Health check DTOs
- `system_log_dto.py` - System logging DTOs

**Đặc điểm**:
- ✅ Sử dụng Pydantic để validation
- ✅ Không chứa business logic
- ✅ Chỉ là data structures
- ✅ Độc lập với infrastructure

**Ví dụ**:
```python
class ChatRequestDTO(BaseModel):
    question: str
    session_id: Optional[str]
    user_id: Optional[str]
    stream: bool = True
```

---

### 2. **Interfaces (Repository Interfaces)** - `interfaces/`

**Vai trò**: Định nghĩa **contracts** (ports) với infrastructure layer

**Files**:
- `vector_store_repository.py` - IVectorStoreRepository
- `llm_repository.py` - ILLMRepository
- `cache_repository.py` - ICacheRepository, ISemanticCacheRepository
- `embedding_repository.py` - IEmbeddingRepository
- `health_repository.py` - IHealthRepository
- `system_log_repository.py` - ISystemLogRepository

**Đặc điểm**:
- ✅ Abstract classes (ABC) với @abstractmethod
- ✅ Định nghĩa **WHAT** (interface), không định nghĩa **HOW** (implementation)
- ✅ Infrastructure layer implement các interfaces này
- ✅ Application layer chỉ biết về interfaces, không biết về implementation

**Ví dụ**:
```python
class IVectorStoreRepository(ABC):
    @abstractmethod
    async def hybrid_search(
        self,
        query: str,
        k: int,
        collection_name: Optional[str] = None
    ) -> List[SearchResultDTO]:
        pass
```

**Lợi ích**:
- ✅ **Dependency Inversion**: Application không phụ thuộc vào infrastructure
- ✅ **Testability**: Dễ mock interfaces trong tests
- ✅ **Flexibility**: Có thể thay đổi implementation mà không ảnh hưởng application

---

### 3. **Use Cases** - `use_cases/`

**Vai trò**: Chứa **business logic** và **orchestration logic**

**Files**:
- `rag_use_case.py` - RAG chat functionality
- `search_use_case.py` - Document search
- `file_upload_use_case.py` - File processing
- `health_check_use_case.py` - Health monitoring
- `system_log_use_case.py` - System logging

**Đặc điểm**:
- ✅ Mỗi use case đại diện cho **một business operation**
- ✅ Orchestrate nhiều repositories/services
- ✅ Không chứa infrastructure details
- ✅ Chỉ phụ thuộc vào interfaces

**Ví dụ - RAGUseCase**:
```python
class RAGUseCase:
    def __init__(
        self,
        search_use_case: SearchUseCase,  # ✅ Dùng use case khác
        llm_service: ILLMRepository,      # ✅ Dùng interface
        cache_service: ISemanticCacheRepository
    ):
        self.search_use_case = search_use_case
        self.llm_service = llm_service
        self.cache_service = cache_service

    async def process_chat(self, request: ChatRequestDTO) -> ChatResponseDTO:
        # 1. Check cache
        # 2. Search documents (dùng SearchUseCase)
        # 3. Build context
        # 4. Generate answer (dùng LLM)
        # 5. Cache response
        # 6. Return response
```

---

## 🎯 VAI TRÒ CHÍNH CỦA APPLICATION LAYER

### 1. **Business Logic Orchestration**

Application Layer **orchestrate** (điều phối) các operations:

```
User Request
  ↓
Application Layer (Use Case)
  ├─→ SearchUseCase (search documents)
  ├─→ LLM Service (generate answer)
  ├─→ Cache Service (cache response)
  └─→ Return Response
```

**Ví dụ**: RAGUseCase orchestrate:
- Search documents (SearchUseCase)
- Build context
- Generate answer (LLM)
- Cache response

---

### 2. **Dependency Inversion**

Application Layer **không phụ thuộc** vào infrastructure:

```
❌ SAI:
Application → MilvusVectorStoreRepository (concrete class)

✅ ĐÚNG:
Application → IVectorStoreRepository (interface)
Infrastructure → MilvusVectorStoreRepository implements IVectorStoreRepository
```

**Lợi ích**:
- ✅ Có thể thay đổi Milvus → Pinecone mà không sửa Application
- ✅ Dễ test (mock interfaces)
- ✅ Loose coupling

---

### 3. **Use Case Pattern**

Mỗi use case đại diện cho **một business operation**:

- `RAGUseCase.process_chat()` - Chat với RAG
- `SearchUseCase.search_documents()` - Tìm kiếm documents
- `FileUploadUseCase.upload_and_process_file()` - Upload và xử lý file
- `HealthCheckUseCase.check_health()` - Kiểm tra health

**Đặc điểm**:
- ✅ Single Responsibility: Mỗi use case làm một việc
- ✅ Reusable: Có thể dùng use case này trong use case khác (RAGUseCase dùng SearchUseCase)
- ✅ Testable: Dễ test từng use case riêng

---

### 4. **Data Transformation**

Application Layer transform data giữa các layers:

```
Presentation Layer (ChatRequest)
  ↓
Application Layer (ChatRequestDTO → SearchRequestDTO)
  ↓
Infrastructure Layer (SearchRequestDTO → Milvus query)
```

**Ví dụ**:
- `ChatRequestDTO` → `SearchRequestDTO` (trong RAGUseCase)
- `SearchResponseDTO` → `ChatResponseDTO` (format response)

---

## 📊 SO SÁNH VỚI CÁC LAYERS KHÁC

| Layer | Vai trò | Phụ thuộc vào |
|-------|---------|---------------|
| **Presentation** | HTTP/WebSocket handlers | Application Layer |
| **Application** | Business logic, Use cases | Domain Layer, Interfaces |
| **Domain** | Core business rules, Entities | Không phụ thuộc gì |
| **Infrastructure** | External services (DB, APIs) | Application interfaces |

---

## ✅ NGUYÊN TẮC THIẾT KẾ

### 1. **Dependency Rule**
- ✅ Application chỉ phụ thuộc vào Domain và Interfaces
- ❌ Application không phụ thuộc vào Infrastructure (concrete classes)
- ❌ Application không phụ thuộc vào Presentation

### 2. **Single Responsibility**
- ✅ Mỗi use case làm một việc
- ✅ Mỗi DTO đại diện cho một data structure

### 3. **Interface Segregation**
- ✅ Interfaces nhỏ, focused
- ✅ Không force implement methods không cần

### 4. **Dependency Injection**
- ✅ Use cases nhận dependencies qua constructor
- ✅ Dùng DI container (dependency-injector)

---

## 🔄 FLOW ĐIỂN HÌNH

### RAG Chat Flow:

```
1. User gửi request
   ↓
2. ChatController (Presentation)
   - Nhận HTTP/WebSocket request
   - Convert to ChatRequestDTO
   ↓
3. RAGUseCase (Application)
   - Check cache
   - Search documents (SearchUseCase)
   - Build context
   - Generate answer (LLM via interface)
   - Cache response
   - Return ChatResponseDTO
   ↓
4. ChatController
   - Convert ChatResponseDTO to HTTP response
   - Return to user
```

**Trong flow này**:
- ✅ Presentation chỉ handle HTTP/WebSocket
- ✅ Application chứa business logic
- ✅ Infrastructure implement interfaces (LLM, Cache, Vector Store)

---

## 📝 TÓM TẮT

**Application Layer là gì?**
- Lớp chứa **business logic** và **use cases**
- Orchestrate các operations
- Transform data giữa layers
- Định nghĩa contracts với infrastructure (interfaces)

**Vai trò chính:**
1. ✅ **Business Logic Orchestration** - Điều phối các operations
2. ✅ **Dependency Inversion** - Dùng interfaces, không phụ thuộc infrastructure
3. ✅ **Use Case Pattern** - Mỗi use case = một business operation
4. ✅ **Data Transformation** - Transform data giữa layers

**Nguyên tắc:**
- ✅ Chỉ phụ thuộc Domain và Interfaces
- ✅ Không phụ thuộc Infrastructure hay Presentation
- ✅ Single Responsibility
- ✅ Dependency Injection

