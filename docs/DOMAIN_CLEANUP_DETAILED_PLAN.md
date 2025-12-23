# Kế hoạch Cleanup Domain Layer - Chi tiết

## 📋 TÓM TẮT

**Tổng số components:** 29
**Được sử dụng:** 4 (chỉ trong MilvusRepository)
**Dư thừa:** 25

**Khuyến nghị:** Xóa 25 components dư thừa, giữ lại 4 components đang được sử dụng

---

## 1. 🗑️ DANH SÁCH CỤ THỂ CẦN XÓA

### 1.1. Domain Events (5 files) - ❌ XÓA HOÀN TOÀN

#### Files cần xóa:
1. ✅ `app/src/domain/events/__init__.py`
2. ✅ `app/src/domain/events/base_event.py`
3. ✅ `app/src/domain/events/rag_events.py`
4. ✅ `app/src/domain/events/retrieval_events.py`
5. ✅ `app/src/domain/events/conversation_events.py`

**Tổng: 5 files (không có subdirectories)**

#### Lý do xóa:
- ❌ **KHÔNG được sử dụng** - Không có code nào emit events
- ❌ **KHÔNG được consume** - Không có code nào listen events
- ❌ **Không có kế hoạch sử dụng** - Chỉ được định nghĩa, không có implementation
- ✅ **Clean code** - Không giữ code không sử dụng
- ✅ **Giảm complexity** - 10 files không cần thiết

#### Impact:
- ✅ **Không ảnh hưởng** - Không có code nào phụ thuộc vào events
- ✅ **An toàn** - Có thể xóa hoàn toàn

---

### 1.2. Domain Services (4 files) - ❌ XÓA HOÀN TOÀN

#### Files cần xóa:
1. ✅ `app/src/domain/services/context_builder.py`
2. ✅ `app/src/domain/services/prompt_builder.py`
3. ✅ `app/src/domain/services/conversation_manager.py`
4. ✅ `app/src/domain/services/retrieval_optimizer.py`

#### Lý do xóa:
- ❌ **Được tạo trong Container nhưng KHÔNG được inject** vào Use Cases
- ❌ **RAGUseCase đã được refactor** để không dùng Domain services (dùng tool calling)
- ❌ **Không có Use Case nào sử dụng** các services này
- ✅ **Clean code** - Xóa code không sử dụng
- ✅ **Giảm confusion** - Tránh nhầm lẫn về dependencies

#### Impact:
- ⚠️ **Cần xóa khỏi Container** - Xóa Domain services khỏi `container.py`
- ✅ **Không ảnh hưởng Use Cases** - Use Cases không phụ thuộc vào services

---

### 1.3. Domain Entities (5/7 files) - ❌ XÓA 5 FILES

#### Files cần xóa:
1. ✅ `app/src/domain/entities/message.py`
2. ✅ `app/src/domain/entities/tool_call.py`
3. ✅ `app/src/domain/entities/chat_session.py`
4. ✅ `app/src/domain/entities/conversation_history.py`
5. ✅ `app/src/domain/entities/embedding_model.py`

#### Files giữ lại:
- ✅ `app/src/domain/entities/document.py` - **Được sử dụng** trong MilvusRepository
- ✅ `app/src/domain/entities/retrieval_result.py` - **Được sử dụng** trong MilvusRepository

#### Lý do xóa:
- ❌ **KHÔNG được sử dụng** trong Application layer
- ❌ **KHÔNG được sử dụng** trong Infrastructure layer (trừ Document, RetrievalResult)
- ❌ **Không có kế hoạch sử dụng** - Chỉ được định nghĩa
- ✅ **Clean code** - Xóa code không sử dụng

#### Lý do giữ lại Document và RetrievalResult:
- ✅ **Được sử dụng** trong `MilvusRepository._convert_langchain_doc_to_domain()`
- ✅ **Được sử dụng** trong `MilvusRepository.search()` method
- ⚠️ **Lưu ý:** MilvusRepository có method `search()` riêng dùng Domain types, nhưng interface yêu cầu `hybrid_search()` với string query - Có thể có mismatch

---

### 1.4. Domain Value Objects (6/8 files) - ❌ XÓA 6 FILES

#### Files cần xóa:
1. ✅ `app/src/domain/value_objects/context.py` (RAGContext)
2. ✅ `app/src/domain/value_objects/session_id.py`
3. ✅ `app/src/domain/value_objects/user_id.py`
4. ✅ `app/src/domain/value_objects/prompt.py`
5. ✅ `app/src/domain/value_objects/retrieval_config.py`
6. ✅ `app/src/domain/value_objects/llm_config.py`

#### Files giữ lại:
- ✅ `app/src/domain/value_objects/search_filter.py` - **Được sử dụng** trong MilvusRepository
- ✅ `app/src/domain/value_objects/query.py` (SearchQuery) - **Được sử dụng** trong MilvusRepository

#### Lý do xóa:
- ❌ **KHÔNG được sử dụng** trong Application layer
- ❌ **KHÔNG được sử dụng** trong Infrastructure layer (trừ SearchQuery, SearchFilter)
- ❌ **Không có kế hoạch sử dụng** - Chỉ được định nghĩa
- ✅ **Clean code** - Xóa code không sử dụng

#### Lý do giữ lại SearchQuery và SearchFilter:
- ✅ **Được sử dụng** trong `MilvusRepository.search()` method
- ⚠️ **Lưu ý:** MilvusRepository có method `search()` riêng dùng Domain types, nhưng interface yêu cầu `hybrid_search()` với string query - Có thể có mismatch

---

## 2. 🔧 CẦN SỬA TRONG CONTAINER

### 2.1. Xóa Domain Services khỏi Container

**File:** `app/src/bootstrap/container.py`

**Cần xóa:**
```python
# Domain Services
context_builder = providers.Factory(
    ContextBuilderService,
    max_context_length=4000,
    include_metadata=True,
    include_scores=True
)

prompt_builder = providers.Factory(
    PromptBuilderService,
    include_context_header=True,
    include_history_header=True
)

conversation_manager = providers.Factory(
    ConversationManagerService,
    max_messages=20,
    summarization_threshold=12
)

retrieval_optimizer = providers.Factory(
    RetrievalOptimizerService,
    min_score_threshold=0.0,
    enable_deduplication=True
)
```

**Xóa imports:**
```python
from app.src.domain.services import (
    ContextBuilderService,
    PromptBuilderService,
    ConversationManagerService,
    RetrievalOptimizerService
)
```

**Lý do:**
- ❌ Services được tạo nhưng không được inject vào Use Cases
- ❌ RAGUseCase không nhận các services này
- ✅ Clean code - Xóa dependencies không sử dụng

---

## 3. ⚠️ VẤN ĐỀ PHÁT HIỆN - CẦN FIX

### 3.1. MilvusRepository Interface Mismatch

**Vấn đề:**
- MilvusRepository import `IVectorStore` nhưng interface thực tế là `IVectorStoreRepository`
- MilvusRepository có method `search(SearchQuery, SearchFilter)` nhưng interface yêu cầu `hybrid_search(query: str, ...)`
- SearchUseCase gọi `vector_store.hybrid_search()` nhưng MilvusRepository không có method này

**Cần fix:**
- ✅ Implement `hybrid_search()` method trong MilvusRepository
- ✅ Hoặc refactor để không dùng Domain types trong MilvusRepository

**Lưu ý:**
- Nếu fix interface mismatch, có thể không cần giữ Domain types trong MilvusRepository
- Nhưng hiện tại MilvusRepository đang dùng Domain types, nên cần giữ lại

---

## 4. 📊 TỔNG KẾT

### 4.1. Files cần xóa (25 files + 1 directory)

**Domain Events (5 files + 1 directory):**
- ✅ `domain/events/__init__.py`
- ✅ `domain/events/base_event.py`
- ✅ `domain/events/rag_events.py`
- ✅ `domain/events/retrieval_events.py`
- ✅ `domain/events/conversation_events.py`

**Domain Services (4 files):**
- ✅ `domain/services/context_builder.py`
- ✅ `domain/services/prompt_builder.py`
- ✅ `domain/services/conversation_manager.py`
- ✅ `domain/services/retrieval_optimizer.py`

**Domain Entities (5 files):**
- ✅ `domain/entities/message.py`
- ✅ `domain/entities/tool_call.py`
- ✅ `domain/entities/chat_session.py`
- ✅ `domain/entities/conversation_history.py`
- ✅ `domain/entities/embedding_model.py`

**Domain Value Objects (6 files):**
- ✅ `domain/value_objects/context.py`
- ✅ `domain/value_objects/session_id.py`
- ✅ `domain/value_objects/user_id.py`
- ✅ `domain/value_objects/prompt.py`
- ✅ `domain/value_objects/retrieval_config.py`
- ✅ `domain/value_objects/llm_config.py`

**Container (1 section):**
- ✅ Xóa Domain services khỏi `container.py`
- ✅ Xóa imports Domain services

**Tổng: 25 files + 1 directory (events/) cần xóa**

---

### 4.2. Files giữ lại (4 files)

**Domain Entities (2 files):**
- ✅ `domain/entities/document.py` - Dùng trong MilvusRepository
- ✅ `domain/entities/retrieval_result.py` - Dùng trong MilvusRepository

**Domain Value Objects (2 files):**
- ✅ `domain/value_objects/query.py` (SearchQuery) - Dùng trong MilvusRepository
- ✅ `domain/value_objects/search_filter.py` - Dùng trong MilvusRepository

**Tổng: 4 files giữ lại**

---

## 5. ✅ LỢI ÍCH SAU KHI CLEANUP

### 5.1. Code Metrics

**Trước cleanup:**
- Events: 10 components
- Entities: 7 components
- Value Objects: 8 components
- Services: 4 components
- **Tổng: 29 components**

**Sau cleanup:**
- Events: 0 components (giảm 100%)
- Entities: 2 components (giảm 71%)
- Value Objects: 2 components (giảm 75%)
- Services: 0 components (giảm 100%)
- **Tổng: 4 components (giảm 86%)**

---

### 5.2. Lợi ích

1. ✅ **Code gọn gàng hơn** - Giảm 86% code không sử dụng
2. ✅ **Dễ maintain** - Ít code hơn, dễ hiểu hơn
3. ✅ **Không có code dư thừa** - Chỉ giữ lại những gì thực sự được sử dụng
4. ✅ **Giảm confusion** - Không có dependencies không sử dụng
5. ✅ **Faster build/test** - Ít files hơn, build nhanh hơn

---

## 6. 🎯 KẾT LUẬN

### Khuyến nghị cuối cùng:

**XÓA:**
- ✅ Tất cả Domain Events (10 events)
- ✅ Tất cả Domain Services (4 services)
- ✅ 5/7 Domain Entities (Message, ToolCall, ChatSession, ConversationHistory, EmbeddingModel)
- ✅ 6/8 Domain Value Objects (RAGContext, SessionId, UserId, Prompt, RetrievalConfig, LLMConfig)
- ✅ Domain services khỏi Container

**GIỮ LẠI:**
- ✅ `Document` entity (dùng trong MilvusRepository)
- ✅ `RetrievalResult` entity (dùng trong MilvusRepository)
- ✅ `SearchQuery` value object (dùng trong MilvusRepository)
- ✅ `SearchFilter` value object (dùng trong MilvusRepository)

**Kết quả:**
- Giảm từ 29 → 4 components (giảm 86%)
- Code clean, không có dư thừa
- Vẫn giữ lại những gì thực sự được sử dụng

