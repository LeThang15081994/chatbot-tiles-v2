# Tại sao Application Layer có thể dùng Domain Services?

## 🎯 CÂU HỎI

**RAGUseCase nằm trong Application Layer, tại sao lại có thể sử dụng Domain services?**

---

## 📐 DEPENDENCY RULE TRONG CLEAN ARCHITECTURE

### Quy tắc cơ bản:

```
┌─────────────────────────────────────┐
│   Presentation Layer (Outer)      │  ← Phụ thuộc vào Application
├─────────────────────────────────────┤
│   Application Layer (Middle)      │  ← Phụ thuộc vào Domain ⭐
├─────────────────────────────────────┤
│   Domain Layer (Inner)             │  ← KHÔNG phụ thuộc gì
├─────────────────────────────────────┤
│   Infrastructure Layer (Outer)     │  ← Implement Application interfaces
└─────────────────────────────────────┘
```

**Dependency Rule (Quy tắc phụ thuộc):**
- ✅ **Outer layers PHẢI phụ thuộc vào Inner layers**
- ❌ **Inner layers KHÔNG phụ thuộc vào Outer layers**

---

## ✅ TẠI SAO APPLICATION CÓ THỂ DÙNG DOMAIN?

### 1. **Domain là Inner Layer**

```
Domain Layer (Inner) ← Application Layer (Outer) phụ thuộc vào đây
```

**Giải thích:**
- Domain Layer là **inner layer** (lớp trong cùng)
- Application Layer là **outer layer** (lớp ngoài)
- Theo Dependency Rule: **Outer layers PHẢI phụ thuộc vào Inner layers**
- ✅ **Application PHẢI phụ thuộc vào Domain** (đúng!)

---

### 2. **Domain Services là Pure Business Logic**

Domain services là **pure Python classes** không phụ thuộc vào:
- ❌ Infrastructure (DB, APIs)
- ❌ Frameworks (FastAPI, Django)
- ❌ External libraries (ngoài Python stdlib)

**Ví dụ:**
```python
# Domain Service - Pure business logic
class ContextBuilderService:
    def __init__(self, max_context_length: int = 4000):
        self.max_context_length = max_context_length

    def build_context(self, documents: List[Document], query: str) -> RAGContext:
        # Pure business logic - không phụ thuộc infrastructure
        # ...
```

**Vì Domain services là pure business logic:**
- ✅ Application có thể import và sử dụng
- ✅ Không vi phạm Dependency Rule
- ✅ Đúng Clean Architecture

---

### 3. **Application Layer NÊN dùng Domain Services**

**Theo Clean Architecture:**
- ✅ Application Layer **orchestrate** business operations
- ✅ Domain Layer **chứa** core business logic
- ✅ Application **NÊN dùng** Domain services cho business logic

**Ví dụ đúng:**
```python
# Application Layer - RAGUseCase
from app.src.domain.services import ContextBuilderService  # ✅ Import Domain

class RAGUseCase:
    def __init__(self, context_builder: ContextBuilderService):  # ✅ Nhận Domain service
        self.context_builder = context_builder

    async def process_chat(self, request: ChatRequestDTO):
        # Orchestrate operations
        search_results = await self.search_use_case.search_documents(...)

        # ✅ Dùng Domain service cho business logic
        context = self.context_builder.build_context(
            documents=search_results,
            query=request.question
        )

        # Continue with LLM...
```

---

## ❌ SO SÁNH: SAI vs ĐÚNG

### ❌ SAI (Hiện tại):

```python
# Application Layer tự implement Domain logic
class RAGUseCase:
    def _build_context(self, search_results):
        # ❌ Tự implement business logic
        context_parts = []
        for idx, result in enumerate(search_results, 1):
            context_parts.append(f"[Document {idx}]")
            context_parts.append(result.content)
        return "\n\n".join(context_parts)
```

**Vấn đề:**
- ❌ Application đang làm việc của Domain
- ❌ Duplicate logic (Domain đã có ContextBuilderService)
- ❌ Vi phạm Single Responsibility

---

### ✅ ĐÚNG (Nên là):

```python
# Application Layer dùng Domain service
from app.src.domain.services import ContextBuilderService

class RAGUseCase:
    def __init__(self, context_builder: ContextBuilderService):  # ✅ Nhận Domain service
        self.context_builder = context_builder

    async def process_chat(self, request: ChatRequestDTO):
        search_results = await self.search_use_case.search_documents(...)

        # ✅ Dùng Domain service
        context = self.context_builder.build_context(
            documents=search_results,
            query=request.question
        )
```

**Lợi ích:**
- ✅ Application chỉ orchestrate
- ✅ Domain chứa business logic
- ✅ Single Responsibility
- ✅ Reusable Domain services

---

## 🔄 DEPENDENCY FLOW

### Flow đúng trong Clean Architecture:

```
1. Presentation Layer
   ↓ depends on
2. Application Layer
   ↓ depends on (✅ ĐÚNG!)
3. Domain Layer
   ↑ implements
4. Infrastructure Layer (implements Application interfaces)
```

**Giải thích:**
- Application **import** Domain services → ✅ Đúng
- Application **sử dụng** Domain services → ✅ Đúng
- Domain **KHÔNG import** Application → ✅ Đúng
- Domain **KHÔNG phụ thuộc** Application → ✅ Đúng

---

## 📊 VÍ DỤ CỤ THỂ

### Domain Service (Inner Layer):

```python
# domain/services/context_builder.py
class ContextBuilderService:
    """Domain service - Pure business logic"""
    def build_context(self, documents: List[Document], query: str) -> RAGContext:
        # Business logic here
        ...
```

### Application Use Case (Outer Layer):

```python
# application/use_cases/rag_use_case.py
from app.src.domain.services import ContextBuilderService  # ✅ Import Domain

class RAGUseCase:
    def __init__(self, context_builder: ContextBuilderService):  # ✅ Nhận Domain service
        self.context_builder = context_builder

    async def process_chat(self, request: ChatRequestDTO):
        # ✅ Sử dụng Domain service
        context = self.context_builder.build_context(documents, query)
```

**Tại sao được?**
- ✅ Domain là inner layer
- ✅ Application là outer layer
- ✅ Outer phụ thuộc Inner → Đúng Dependency Rule

---

## 🎯 KẾT LUẬN

### Tại sao Application có thể dùng Domain?

1. ✅ **Dependency Rule**: Outer layers (Application) PHẢI phụ thuộc Inner layers (Domain)
2. ✅ **Domain là Pure**: Domain services không phụ thuộc infrastructure
3. ✅ **Đúng Clean Architecture**: Application orchestrate, Domain chứa business logic

### Tại sao NÊN dùng Domain services?

1. ✅ **Single Responsibility**: Application orchestrate, Domain chứa logic
2. ✅ **Reusability**: Domain services có thể dùng ở nhiều nơi
3. ✅ **Testability**: Domain services dễ test (pure logic)
4. ✅ **Maintainability**: Logic tập trung ở Domain

### Tại sao KHÔNG nên tự implement?

1. ❌ **Duplicate logic**: Logic bị duplicate giữa Application và Domain
2. ❌ **Vi phạm SRP**: Application đang làm việc của Domain
3. ❌ **Khó maintain**: Logic rải rác ở nhiều nơi

---

## ✅ TÓM TẮT

**Câu hỏi**: RAGUseCase (Application) có thể dùng Domain services không?

**Trả lời**: ✅ **CÓ, và NÊN dùng!**

**Lý do:**
1. ✅ Dependency Rule: Application (outer) PHẢI phụ thuộc Domain (inner)
2. ✅ Domain services là pure business logic, không phụ thuộc infrastructure
3. ✅ Đúng Clean Architecture: Application orchestrate, Domain chứa logic

**Hiện tại:**
- ❌ RAGUseCase tự implement Domain logic → SAI
- ✅ Nên dùng Domain services → ĐÚNG

