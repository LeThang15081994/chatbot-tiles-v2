# 🎯 Kiến trúc đơn giản hóa cho Chatbot RAG

## 📋 Yêu cầu
- **Mục đích**: Chatbot RAG cho knowledge base về gạch ốp lát
- **Upload tài liệu**: Thủ công (không qua API)
- **Mục tiêu**: Đơn giản hóa, tập trung vào chatbot, bỏ phần upload/quản lý tài liệu

---

## ✅ USE CASES NÊN GIỮ

### 1. **RAGUseCase** - ⭐ CỐT LÕI
**Mục đích**: Chatbot chính với RAG
**Chức năng**:
- `process_chat()` - Chat non-streaming
- `stream_chat()` - Chat streaming (WebSocket)
- `get_chat_history()` - Lịch sử chat

**Lý do giữ**: Đây là use case chính của hệ thống

---

### 2. **SearchUseCase** - ✅ CẦN THIẾT
**Mục đích**: Tìm kiếm documents trong vector store
**Chức năng**:
- `search_documents()` - Hybrid search
- `vector_search()` - Vector search only
- `hybrid_search()` - Vector + BM25

**Lý do giữ**:
- RAGUseCase cần search để retrieve documents
- Có thể dùng cho API search riêng (nếu cần)

---

### 3. **HealthCheckUseCase** - ✅ CẦN THIẾT
**Mục đích**: Monitoring và health checks
**Chức năng**:
- `check_health()` - Health check tổng thể
- `check_readiness()` - Readiness check
- `check_liveness()` - Liveness check

**Lý do giữ**: Cần thiết cho production monitoring

---

## ❌ USE CASES NÊN BỎ/TẠM HOÃN

### 4. **FileUploadUseCase** - ⏸️ TẠM HOÃN
**Lý do bỏ**:
- Upload tài liệu thủ công (không qua API)
- Có thể phát triển sau khi chatbot ổn định

**Hành động**:
- Giữ file code (không xóa)
- Không wire trong container
- Comment trong code: `# TODO: Implement when needed`

---

### 5. **SystemLogUseCase** - ⏸️ TẠM HOÃN (Optional)
**Lý do bỏ**:
- Không critical cho MVP
- Có thể dùng logging thông thường (file logs)

**Hành động**:
- Giữ file code (không xóa)
- Không wire trong container
- HealthController không cần SystemLogUseCase

---

## 🎨 CONTROLLERS NÊN GIỮ/ĐƠN GIẢN HÓA

### 1. **ChatController** - ✅ GIỮ NGUYÊN
**Chức năng giữ**:
- `chat()` - REST chat
- `chat_stream()` - WebSocket streaming
- `get_conversation_history()` - Lịch sử
- `clear_conversation()` - Xóa lịch sử

---

### 2. **DocumentController** - ⚠️ ĐƠN GIẢN HÓA
**Chức năng GIỮ**:
- ✅ `search_documents()` - Tìm kiếm documents

**Chức năng BỎ**:
- ❌ `upload_document()` - Upload (không cần)
- ❌ `get_document()` - Get by ID (không cần)
- ❌ `delete_document()` - Delete (không cần)
- ❌ `list_documents()` - List all (không cần)

**Lý do**: Chỉ cần search để hỗ trợ RAG, không cần CRUD documents

---

### 3. **HealthController** - ✅ GIỮ NGUYÊN
**Chức năng giữ**:
- `health_check()` - Health check
- `readiness_check()` - Readiness
- `liveness_check()` - Liveness

**Lưu ý**: Không cần SystemLogUseCase, chỉ check services cơ bản

---

## 📦 CẤU TRÚC CONTAINER ĐỀ XUẤT

```python
class Container(containers.DeclarativeContainer):
    # ... Infrastructure services ...

    # ✅ USE CASES - CHỈ GIỮ 3 CÁI
    rag_use_case = providers.Factory(
        RAGUseCase,
        vector_store=milvus_repository,
        llm_client=llm_client,
        cache=redis_cache,
        langfuse_service=langfuse_service,
        guardrails_service=guardrails_service,
        context_builder=context_builder,
        prompt_builder=prompt_builder,
        conversation_manager=conversation_manager,
        retrieval_optimizer=retrieval_optimizer
    )

    search_use_case = providers.Factory(
        SearchUseCase,
        vector_store=milvus_repository,
        cache=redis_cache
    )

    health_check_use_case = providers.Factory(
        HealthCheckUseCase,
        vector_store=milvus_repository,
        cache=redis_cache,
        llm_client=llm_client,
        database=database
    )

    # ⏸️ TẠM HOÃN - KHÔNG WIRE
    # file_upload_use_case = ...  # TODO: Implement when needed
    # system_log_use_case = ...   # TODO: Implement when needed

    # ✅ CONTROLLERS
    chat_controller = providers.Factory(
        ChatController,
        rag_use_case=rag_use_case  # Fix: Đổi tên parameter
    )

    document_controller = providers.Factory(
        DocumentController,
        search_use_case=search_use_case  # Fix: Đổi tên parameter, chỉ search
    )

    health_controller = providers.Factory(
        HealthController,
        health_check_use_case=health_check_use_case,  # Fix: Dùng use case
        embedding_service=embedding_service,
        milvus_repository=milvus_repository,
        redis_repository=redis_cache
    )
```

---

## 🔧 CẦN SỬA

### 1. Fix ChatController
```python
# chat_controller.py
from src.application.use_cases.rag_use_case import RAGUseCase  # ✅ Đổi import

class ChatController:
    def __init__(self, rag_use_case: RAGUseCase):  # ✅ Đổi tên parameter
        self.rag_use_case = rag_use_case

    async def chat(self, request: ChatRequest):
        result = await self.rag_use_case.process_chat(...)  # ✅ Dùng RAGUseCase
```

### 2. Đơn giản hóa DocumentController
```python
# document_controller.py
from src.application.use_cases.search_use_case import SearchUseCase  # ✅ Đổi import

class DocumentController:
    def __init__(self, search_use_case: SearchUseCase):  # ✅ Đổi tên parameter
        self.search_use_case = search_use_case

    # ✅ CHỈ GIỮ search_documents()
    async def search_documents(self, request: SearchRequest):
        return await self.search_use_case.search_documents(...)

    # ❌ BỎ các methods: upload_document, get_document, delete_document, list_documents
    # Comment: # TODO: Implement document management when needed
```

### 3. Fix HealthController
```python
# health_controller.py
from src.application.use_cases.health_check_use_case import HealthCheckUseCase

class HealthController:
    def __init__(
        self,
        health_check_use_case: HealthCheckUseCase,  # ✅ Dùng use case
        embedding_service,
        milvus_repository,
        redis_repository,
    ):
        self.health_check_use_case = health_check_use_case
        # ... other services for direct checks if needed

    async def health_check(self):
        return await self.health_check_use_case.check_health()  # ✅ Dùng use case
```

### 4. Đơn giản hóa Document Router
```python
# document_router.py
router = APIRouter(prefix="/documents", tags=["Documents"])

# ✅ CHỈ GIỮ search endpoint
@router.post("/search", response_model=SearchResponse)
async def search_documents(...):
    ...

# ❌ BỎ các endpoints: /upload, /upload/file, /{document_id}, DELETE /{document_id}, GET /
# Comment: # TODO: Implement document management endpoints when needed
```

---

## 📊 TỔNG KẾT

### Use Cases:
- ✅ **RAGUseCase** - Giữ (cốt lõi)
- ✅ **SearchUseCase** - Giữ (cần cho RAG)
- ✅ **HealthCheckUseCase** - Giữ (monitoring)
- ⏸️ **FileUploadUseCase** - Tạm hoãn (không wire)
- ⏸️ **SystemLogUseCase** - Tạm hoãn (không wire)

### Controllers:
- ✅ **ChatController** - Giữ nguyên
- ⚠️ **DocumentController** - Đơn giản hóa (chỉ search)
- ✅ **HealthController** - Giữ, dùng HealthCheckUseCase

### Routers:
- ✅ **ChatRouter** - Giữ nguyên
- ⚠️ **DocumentRouter** - Đơn giản hóa (chỉ /search)
- ✅ **HealthRouter** - Giữ nguyên

---

## 🎯 LỢI ÍCH

1. **Đơn giản hóa**: Chỉ giữ những gì cần thiết cho chatbot
2. **Dễ maintain**: Ít code, ít dependencies
3. **Tập trung**: Focus vào core functionality (RAG chat)
4. **Mở rộng sau**: Có thể thêm upload/quản lý documents sau

---

## 📝 CHECKLIST THỰC HIỆN

- [ ] Fix ChatController: Đổi import và parameter name
- [ ] Đơn giản hóa DocumentController: Bỏ upload/CRUD, chỉ giữ search
- [ ] Fix HealthController: Dùng HealthCheckUseCase
- [ ] Đơn giản hóa DocumentRouter: Bỏ upload/CRUD endpoints
- [ ] Update Container: Bỏ wire FileUploadUseCase và SystemLogUseCase
- [ ] Test: Đảm bảo chatbot và search hoạt động
- [ ] Comment code: Đánh dấu TODO cho features tạm hoãn

