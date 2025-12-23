# Kiểm tra vi phạm Clean Architecture trong Application Layer

## 🎯 NGUYÊN TẮC KIỂM TRA

**Theo Clean Architecture:**
1. ✅ Application Layer **PHẢI phụ thuộc vào** Domain Layer
2. ✅ Application Layer **KHÔNG CHỨA** Domain Layer (Domain là layer riêng)
3. ✅ Application Layer **NÊN dùng** Domain services cho core business logic

---

## ❌ VẤN ĐỀ PHÁT HIỆN

### 1. **Application Layer KHÔNG dùng Domain Services**

#### Vấn đề:
- ✅ **Container có định nghĩa Domain services**:
  - `ContextBuilderService`
  - `PromptBuilderService`
  - `ConversationManagerService`
  - `RetrievalOptimizerService`

- ❌ **RAGUseCase KHÔNG nhận Domain services**:
  ```python
  # container.py - Domain services được tạo
  context_builder = providers.Factory(ContextBuilderService, ...)
  prompt_builder = providers.Factory(PromptBuilderService, ...)
  conversation_manager = providers.Factory(ConversationManagerService, ...)
  retrieval_optimizer = providers.Factory(RetrievalOptimizerService, ...)

  # container.py - RAGUseCase KHÔNG nhận Domain services
  rag_use_case = providers.Factory(
      RAGUseCase,
      search_use_case=search_use_case,
      llm_service=llm_client,
      cache_service=redis_cache
      # ❌ THIẾU: context_builder, prompt_builder, conversation_manager
  )
  ```

#### Hậu quả:
- ❌ **RAGUseCase tự implement business logic** thay vì dùng Domain services
- ❌ **Duplicate logic** - Business logic bị duplicate giữa Application và Domain
- ❌ **Vi phạm Single Responsibility** - Application đang làm việc của Domain

---

### 2. **RAGUseCase tự implement Domain logic**

#### Vấn đề trong `rag_use_case.py`:

**A. `_build_context()` method:**
```python
# ❌ RAGUseCase tự implement context building
def _build_context(
    self,
    search_results: List[Any],
    products_metadata: List[Dict[str, Any]]
) -> str:
    # Logic build context - ĐÂY LÀ DOMAIN LOGIC!
    context_parts = []
    for idx, result in enumerate(search_results, 1):
        context_parts.append(f"[Document {idx}]")
        context_parts.append(result.content)
        # Extract product metadata...
    return "\n\n".join(context_parts)
```

**Nên dùng:**
```python
# ✅ Dùng Domain service
def _build_context(self, search_results):
    return self.context_builder.build_context(search_results)
```

**B. `_prepare_messages()` method:**
```python
# ❌ RAGUseCase tự implement prompt building
def _prepare_messages(
    self,
    question: str,
    context: str,
    session_id: Optional[str] = None
) -> List[ChatMessageDTO]:
    # Logic build prompt - ĐÂY LÀ DOMAIN LOGIC!
    system_prompt = """You are a helpful assistant..."""
    if context:
        system_prompt += f"\n\nContext:\n{context}"
    # ...
```

**Nên dùng:**
```python
# ✅ Dùng Domain service
def _prepare_messages(self, question, context, session_id):
    return self.prompt_builder.build_messages(question, context, session_id)
```

---

## ✅ SO SÁNH: ĐÚNG vs SAI

### ❌ SAI (Hiện tại):

```
Application Layer (RAGUseCase)
  ├─→ Tự implement _build_context()      ❌ Domain logic trong Application
  ├─→ Tự implement _prepare_messages()  ❌ Domain logic trong Application
  └─→ Chỉ dùng Interfaces (OK)
```

**Vấn đề:**
- Application Layer chứa Domain logic
- Domain services không được sử dụng
- Duplicate logic

---

### ✅ ĐÚNG (Nên là):

```
Application Layer (RAGUseCase)
  ├─→ Dùng ContextBuilderService        ✅ Domain service
  ├─→ Dùng PromptBuilderService         ✅ Domain service
  ├─→ Dùng ConversationManagerService   ✅ Domain service
  └─→ Dùng Interfaces (OK)
```

**Lợi ích:**
- Application Layer chỉ orchestrate
- Domain logic ở Domain Layer
- Single Responsibility
- Reusable Domain services

---

## 🔧 CÁCH SỬA

### 1. **Refactor RAGUseCase để nhận Domain services**

```python
class RAGUseCase:
    def __init__(
        self,
        search_use_case: SearchUseCase,
        llm_service: ILLMRepository,
        cache_service: Optional[ISemanticCacheRepository] = None,
        # ✅ Thêm Domain services
        context_builder: ContextBuilderService = None,
        prompt_builder: PromptBuilderService = None,
        conversation_manager: ConversationManagerService = None
    ):
        self.search_use_case = search_use_case
        self.llm_service = llm_service
        self.cache_service = cache_service
        # ✅ Inject Domain services
        self.context_builder = context_builder
        self.prompt_builder = prompt_builder
        self.conversation_manager = conversation_manager
```

### 2. **Dùng Domain services thay vì tự implement**

```python
# ❌ TRƯỚC
def _build_context(self, search_results, products_metadata):
    # Tự implement logic
    context_parts = []
    for idx, result in enumerate(search_results, 1):
        context_parts.append(f"[Document {idx}]")
        context_parts.append(result.content)
    return "\n\n".join(context_parts)

# ✅ SAU
def _build_context(self, search_results, products_metadata):
    # Dùng Domain service
    if self.context_builder:
        return self.context_builder.build_context(search_results)
    else:
        # Fallback nếu không có Domain service
        return self._build_context_fallback(search_results)
```

### 3. **Cập nhật Container**

```python
rag_use_case = providers.Factory(
    RAGUseCase,
    search_use_case=search_use_case,
    llm_service=llm_client,
    cache_service=redis_cache,
    # ✅ Inject Domain services
    context_builder=context_builder,
    prompt_builder=prompt_builder,
    conversation_manager=conversation_manager
)
```

---

## 📊 TỔNG KẾT VI PHẠM

| Vấn đề | Mức độ | Trạng thái |
|--------|--------|------------|
| **Application không dùng Domain services** | ❌ Nghiêm trọng | Cần fix |
| **RAGUseCase tự implement Domain logic** | ❌ Nghiêm trọng | Cần fix |
| **Duplicate logic** | ⚠️ Trung bình | Cần fix |
| **Container không inject Domain services** | ❌ Nghiêm trọng | Cần fix |

---

## ✅ KẾT LUẬN

**Application Layer hiện tại:**
- ✅ **KHÔNG chứa Domain Layer** (đúng - Domain là layer riêng)
- ❌ **KHÔNG dùng Domain services** (sai - nên dùng)
- ❌ **Tự implement Domain logic** (sai - vi phạm Clean Architecture)

**Vi phạm:**
1. ❌ Application Layer đang tự implement business logic thay vì dùng Domain services
2. ❌ Domain services đã được tạo nhưng không được sử dụng
3. ❌ Duplicate logic giữa Application và Domain

**Cần sửa:**
1. ✅ Refactor RAGUseCase để nhận Domain services
2. ✅ Dùng Domain services thay vì tự implement
3. ✅ Cập nhật Container để inject Domain services

**Mức độ vi phạm**: ⚠️ **Nghiêm trọng** - Cần refactor để đúng Clean Architecture

