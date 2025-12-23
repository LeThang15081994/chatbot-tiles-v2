# Báo cáo sử dụng Use Cases trong hệ thống

## 📊 TỔNG QUAN

Hệ thống có **5 use cases** nhưng chỉ **2 use cases được sử dụng thực tế**:

1. ✅ **RAGUseCase** - Được sử dụng (qua ChatController)
2. ✅ **SearchUseCase** - Được sử dụng (qua DocumentController)
3. ✅ **HealthCheckUseCase** - Được tạo nhưng không được inject vào controller
4. ❌ **FileUploadUseCase** - KHÔNG được wire trong container, KHÔNG được sử dụng
5. ❌ **SystemLogUseCase** - Được tạo nhưng pass `None` vào HealthController

---

## 🔴 VẤN ĐỀ PHÁT HIỆN

### 1. MISMATCH giữa Controllers và Use Cases

#### ❌ ChatController vs RAGUseCase
**Vấn đề:**
- `ChatController` import `ChatUseCase` (không tồn tại)
- Container inject `rag_use_case` nhưng với tên parameter `chat_use_case`
- **Sẽ lỗi runtime** khi controller khởi tạo

**Code hiện tại:**
```python
# chat_controller.py
from src.application.use_cases import ChatUseCase  # ❌ Không tồn tại

class ChatController:
    def __init__(self, chat_use_case: ChatUseCase):  # ❌ Expect ChatUseCase
        self.chat_use_case = chat_use_case

# container.py
chat_controller = providers.Factory(
    ChatController,
    chat_use_case=rag_use_case  # ✅ Pass RAGUseCase nhưng tên không match
)
```

**Giải pháp:**
- Option 1: Đổi `ChatController` để nhận `RAGUseCase`
- Option 2: Tạo alias `ChatUseCase = RAGUseCase`
- Option 3: Tạo wrapper `ChatUseCase` wrap `RAGUseCase`

#### ❌ DocumentController vs SearchUseCase
**Vấn đề:**
- `DocumentController` import `DocumentUseCase` (không tồn tại)
- Container inject `search_use_case` nhưng với tên parameter `document_use_case`
- **Sẽ lỗi runtime** khi controller khởi tạo

**Code hiện tại:**
```python
# document_controller.py
from src.application.use_cases import DocumentUseCase  # ❌ Không tồn tại

class DocumentController:
    def __init__(self, document_use_case: DocumentUseCase):  # ❌ Expect DocumentUseCase
        self.document_use_case = document_use_case

# container.py
document_controller = providers.Factory(
    DocumentController,
    document_use_case=search_use_case  # ✅ Pass SearchUseCase nhưng tên không match
)
```

**Giải pháp:**
- Option 1: Đổi `DocumentController` để nhận `SearchUseCase`
- Option 2: Tạo alias `DocumentUseCase = SearchUseCase`
- Option 3: Tạo wrapper `DocumentUseCase` wrap `SearchUseCase`

---

### 2. HealthCheckUseCase - KHÔNG được sử dụng

**Vấn đề:**
- `HealthCheckUseCase` được tạo trong container
- `HealthController` KHÔNG nhận `HealthCheckUseCase`
- `HealthController` tự implement health check logic thay vì dùng use case

**Code hiện tại:**
```python
# container.py
health_check_use_case = providers.Factory(
    HealthCheckUseCase,  # ✅ Được tạo
    ...
)

# health_controller.py
class HealthController:
    def __init__(
        self,
        embedding_service,      # ❌ Trực tiếp inject services
        milvus_repository,      # ❌ Thay vì dùng use case
        redis_repository,
        system_log_use_case,
    ):
        # Tự implement health check thay vì dùng HealthCheckUseCase
```

**Giải pháp:**
- Refactor `HealthController` để sử dụng `HealthCheckUseCase`
- Hoặc xóa `HealthCheckUseCase` nếu không cần

---

### 3. FileUploadUseCase - KHÔNG được wire

**Vấn đề:**
- `FileUploadUseCase` tồn tại nhưng **KHÔNG được wire trong container**
- `DocumentController.upload_document()` gọi `document_use_case.upload_document()`
- Nhưng `document_use_case` là `SearchUseCase` (không có method `upload_document`)
- **Sẽ lỗi runtime** khi gọi upload endpoint

**Code hiện tại:**
```python
# file_upload_use_case.py
class FileUploadUseCase:  # ✅ Tồn tại
    async def upload_and_process_file(...):
        ...

# container.py
# ❌ KHÔNG có file_upload_use_case = providers.Factory(...)

# document_controller.py
async def upload_document(self, request):
    result = await self.document_use_case.upload_document(...)
    # ❌ SearchUseCase không có upload_document()
```

**Giải pháp:**
- Wire `FileUploadUseCase` trong container
- Inject vào `DocumentController` hoặc tạo controller riêng

---

### 4. SystemLogUseCase - Pass None

**Vấn đề:**
- `SystemLogUseCase` tồn tại nhưng **pass `None` vào HealthController**
- `HealthController` gọi `self.system_log_use_case.health_check()`
- **Sẽ lỗi runtime** (AttributeError: 'NoneType' object has no attribute 'health_check')

**Code hiện tại:**
```python
# container.py
health_controller = providers.Factory(
    HealthController,
    ...
    system_log_use_case=None,  # ❌ Pass None
)

# health_controller.py
async def health_check(self):
    postgres_healthy = await self.system_log_use_case.health_check()
    # ❌ None.health_check() sẽ lỗi
```

**Giải pháp:**
- Wire `SystemLogUseCase` trong container
- Inject vào `HealthController`

---

## 📋 TỔNG KẾT VẤN ĐỀ

| Use Case | Status | Được sử dụng? | Vấn đề |
|----------|--------|---------------|--------|
| **RAGUseCase** | ✅ Tồn tại | ✅ Có (ChatController) | ⚠️ Mismatch tên: ChatController expect `ChatUseCase` |
| **SearchUseCase** | ✅ Tồn tại | ✅ Có (DocumentController) | ⚠️ Mismatch tên: DocumentController expect `DocumentUseCase` |
| **HealthCheckUseCase** | ✅ Tồn tại | ❌ Không | ❌ HealthController không dùng, tự implement |
| **FileUploadUseCase** | ✅ Tồn tại | ❌ Không | ❌ Không được wire, không có controller sử dụng |
| **SystemLogUseCase** | ✅ Tồn tại | ⚠️ Một phần | ❌ Pass None vào HealthController, sẽ lỗi runtime |

---

## ✅ ĐỀ XUẤT GIẢI PHÁP

### 1. Fix ChatController và DocumentController

**Option A: Đổi tên parameter trong controllers**
```python
# chat_controller.py
class ChatController:
    def __init__(self, rag_use_case: RAGUseCase):  # ✅ Đổi tên
        self.rag_use_case = rag_use_case

# document_controller.py
class DocumentController:
    def __init__(self, search_use_case: SearchUseCase):  # ✅ Đổi tên
        self.search_use_case = search_use_case
```

**Option B: Tạo type aliases**
```python
# application/use_cases/__init__.py
from .rag_use_case import RAGUseCase as ChatUseCase
from .search_use_case import SearchUseCase as DocumentUseCase
```

### 2. Wire FileUploadUseCase

```python
# container.py
file_upload_use_case = providers.Factory(
    FileUploadUseCase,
    vector_store=milvus_repository,
    embedding_service=embedding_service
)

# Option A: Inject vào DocumentController
document_controller = providers.Factory(
    DocumentController,
    document_use_case=search_use_case,
    file_upload_use_case=file_upload_use_case  # ✅ Thêm
)

# Option B: Tạo controller riêng
file_upload_controller = providers.Factory(
    FileUploadController,
    file_upload_use_case=file_upload_use_case
)
```

### 3. Wire SystemLogUseCase

```python
# container.py
system_log_use_case = providers.Factory(
    SystemLogUseCase,
    log_repository=system_log_repository  # Cần tạo repository
)

health_controller = providers.Factory(
    HealthController,
    ...
    system_log_use_case=system_log_use_case  # ✅ Thay None
)
```

### 4. Refactor HealthController để dùng HealthCheckUseCase

```python
# health_controller.py
class HealthController:
    def __init__(self, health_check_use_case: HealthCheckUseCase):
        self.health_check_use_case = health_check_use_case

    async def health_check(self):
        return await self.health_check_use_case.check_health()
```

---

## 🎯 KẾT LUẬN

**Vấn đề chính:**
1. ❌ **3/5 use cases không được sử dụng đúng cách**
2. ❌ **Mismatch tên giữa controllers và use cases** → Sẽ lỗi runtime
3. ❌ **FileUploadUseCase không được wire** → Upload endpoint sẽ lỗi
4. ❌ **SystemLogUseCase pass None** → Health check sẽ lỗi

**Hành động cần thiết:**
1. ✅ Fix mismatch tên trong controllers
2. ✅ Wire FileUploadUseCase
3. ✅ Wire SystemLogUseCase
4. ✅ Refactor HealthController để dùng HealthCheckUseCase

