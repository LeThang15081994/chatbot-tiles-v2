# Phân tích sử dụng Domain Layer

## 📋 MỤC ĐÍCH

Phân tích Domain Layer để xác định:
1. Domain Events có mục đích sử dụng gì?
2. Domain có bị dư thừa không?

---

## 1. 🔍 DOMAIN EVENTS - Mục đích và sử dụng

### 1.1. Mục đích của Domain Events

**Domain Events** trong Clean Architecture/DDD có mục đích:

1. **Event-Driven Architecture**
   - Decouple components
   - Enable async processing
   - Support event sourcing

2. **Observability & Tracing**
   - Track important domain occurrences
   - Log business events
   - Monitor system behavior

3. **Side Effects Handling**
   - Trigger notifications
   - Update read models
   - Send analytics

4. **Audit Trail**
   - Record what happened
   - When it happened
   - Who/what triggered it

### 1.2. Events được định nghĩa

**Base Event:**
- ✅ `DomainEvent` - Base class với metadata

**Retrieval Events (3):**
- ✅ `DocumentRetrievedEvent` - Documents retrieved
- ✅ `RetrievalCompletedEvent` - Retrieval completed
- ✅ `RetrievalFailedEvent` - Retrieval failed

**Conversation Events (4):**
- ✅ `MessageReceivedEvent` - Message received
- ✅ `ResponseGeneratedEvent` - Response generated
- ✅ `ConversationStartedEvent` - Conversation started
- ✅ `ConversationEndedEvent` - Conversation ended

**RAG Events (3):**
- ✅ `RAGQueryReceivedEvent` - RAG query received
- ✅ `RAGContextBuiltEvent` - Context built
- ✅ `RAGResponseGeneratedEvent` - RAG response generated

**Tổng: 10 events**

### 1.3. Events có được sử dụng không?

**❌ KHÔNG - Events KHÔNG được sử dụng trong code:**

```bash
# Tìm kiếm trong Application layer
grep -r "DomainEvent\|DocumentRetrievedEvent\|RAGQueryReceivedEvent" app/src/application/
# → Không có kết quả

# Tìm kiếm trong Infrastructure layer
grep -r "DomainEvent\|DocumentRetrievedEvent" app/src/infrastructure/
# → Không có kết quả

# Tìm kiếm trong Presentation layer
grep -r "DomainEvent" app/src/presentation/
# → Không có kết quả
```

**Kết luận:**
- ⚠️ Events được định nghĩa nhưng **KHÔNG được emit**
- ⚠️ Events được định nghĩa nhưng **KHÔNG được consume**
- ⚠️ Chỉ được đề cập trong documentation

---

## 2. 📊 PHÂN TÍCH DOMAIN LAYER - Có bị dư không?

### 2.1. Entities (7 entities)

| Entity | Được sử dụng? | Nơi sử dụng | Ghi chú |
|--------|--------------|-------------|---------|
| `Document` | ⚠️ Có thể | Domain services | Được định nghĩa nhưng không được sử dụng trong Application |
| `Message` | ❌ Không | - | Không được import trong Application |
| `ToolCall` | ❌ Không | - | Không được import trong Application |
| `ChatSession` | ❌ Không | - | Không được import trong Application |
| `ConversationHistory` | ❌ Không | - | Không được import trong Application |
| `RetrievalResult` | ❌ Không | - | Không được import trong Application |
| `EmbeddingModel` | ❌ Không | - | Không được import trong Application |

**Kết luận:**
- ❌ **7/7 entities KHÔNG được sử dụng** trong Application layer
- ⚠️ Chỉ được định nghĩa nhưng không được import/sử dụng

---

### 2.2. Value Objects (8 value objects)

| Value Object | Được sử dụng? | Nơi sử dụng | Ghi chú |
|--------------|--------------|-------------|---------|
| `RAGContext` | ⚠️ Có thể | Domain services | Được định nghĩa nhưng không được sử dụng trong Application |
| `SessionId` | ❌ Không | - | Không được import |
| `UserId` | ❌ Không | - | Không được import |
| `SearchQuery` | ❌ Không | - | Không được import |
| `Prompt` | ❌ Không | - | Không được import |
| `RetrievalConfig` | ❌ Không | - | Không được import |
| `LLMConfig` | ❌ Không | - | Không được import |
| `SearchFilter` | ❌ Không | - | Không được import |

**Kết luận:**
- ❌ **8/8 value objects KHÔNG được sử dụng** trong Application layer

---

### 2.3. Domain Services (4 services)

| Service | Được sử dụng? | Nơi sử dụng | Ghi chú |
|---------|--------------|-------------|---------|
| `ContextBuilderService` | ❌ Không | - | Đã bị xóa khỏi RAGUseCase trong refactor |
| `PromptBuilderService` | ❌ Không | - | Đã bị xóa khỏi RAGUseCase trong refactor |
| `ConversationManagerService` | ❌ Không | - | Đã bị xóa khỏi RAGUseCase trong refactor |
| `RetrievalOptimizerService` | ❌ Không | - | Không được sử dụng |

**Kết luận:**
- ❌ **4/4 domain services KHÔNG được sử dụng** trong Application layer
- ⚠️ Đã bị xóa khỏi RAGUseCase khi refactor để dùng tool calling

---

### 2.4. Domain Events (10 events)

| Event | Được sử dụng? | Nơi sử dụng | Ghi chú |
|-------|--------------|-------------|---------|
| `DomainEvent` | ❌ Không | - | Base class, không được sử dụng |
| `DocumentRetrievedEvent` | ❌ Không | - | Không được emit |
| `RetrievalCompletedEvent` | ❌ Không | - | Không được emit |
| `RetrievalFailedEvent` | ❌ Không | - | Không được emit |
| `MessageReceivedEvent` | ❌ Không | - | Không được emit |
| `ResponseGeneratedEvent` | ❌ Không | - | Không được emit |
| `ConversationStartedEvent` | ❌ Không | - | Không được emit |
| `ConversationEndedEvent` | ❌ Không | - | Không được emit |
| `RAGQueryReceivedEvent` | ❌ Không | - | Không được emit |
| `RAGContextBuiltEvent` | ❌ Không | - | Không được emit |
| `RAGResponseGeneratedEvent` | ❌ Không | - | Không được emit |

**Kết luận:**
- ❌ **10/10 events KHÔNG được sử dụng**

---

## 3. 🎯 TỔNG KẾT

### 3.1. Domain Events

**Mục đích:**
- ✅ Event-driven architecture
- ✅ Observability & tracing
- ✅ Side effects handling
- ✅ Audit trail

**Thực tế:**
- ❌ **KHÔNG được sử dụng** - Chỉ được định nghĩa
- ❌ **KHÔNG được emit** trong Application layer
- ❌ **KHÔNG được consume** trong Infrastructure layer

**Kết luận:**
- ⚠️ **Domain Events là DƯ THỪA** trong codebase hiện tại
- ⚠️ Có thể giữ lại nếu có kế hoạch implement event-driven architecture trong tương lai
- ⚠️ Hoặc có thể xóa nếu không có kế hoạch sử dụng

---

### 3.2. Domain Layer - Có bị dư không?

**Tổng số components:**
- Entities: 7
- Value Objects: 8
- Services: 4
- Events: 10
- **Tổng: 29 components**

**Được sử dụng:**
- ❌ **0/29 components được sử dụng** trong Application layer

**Kết luận:**
- ⚠️ **Domain Layer gần như HOÀN TOÀN DƯ THỪA**
- ⚠️ Tất cả components chỉ được định nghĩa nhưng không được sử dụng
- ⚠️ Application layer hiện tại không phụ thuộc vào Domain layer

---

## 4. 💡 KHUYẾN NGHỊ

### 4.1. Domain Events

**Option 1: Xóa (nếu không có kế hoạch sử dụng)**
- ✅ Giảm code complexity
- ✅ Dễ maintain
- ❌ Mất khả năng event-driven architecture

**Option 2: Giữ lại (nếu có kế hoạch sử dụng)**
- ✅ Sẵn sàng cho event-driven architecture
- ✅ Có thể dùng cho observability
- ❌ Code dư thừa hiện tại

**Khuyến nghị:**
- ⚠️ **XÓA** nếu không có kế hoạch implement event-driven architecture trong 6 tháng tới
- ⚠️ **GIỮ LẠI** nếu có kế hoạch implement trong tương lai gần

---

### 4.2. Domain Layer khác

**Entities:**
- ⚠️ `Document` - Có thể dùng trong tương lai (hiện tại không dùng)
- ❌ `Message`, `ToolCall`, `ChatSession`, etc. - Không được sử dụng

**Value Objects:**
- ⚠️ `RAGContext` - Có thể dùng trong tương lai (hiện tại không dùng)
- ❌ Các value objects khác - Không được sử dụng

**Services:**
- ❌ Tất cả services không được sử dụng (đã bị xóa khỏi RAGUseCase)

**Khuyến nghị:**
- ⚠️ **XÓA** các components không được sử dụng
- ⚠️ **GIỮ LẠI** nếu có kế hoạch refactor để sử dụng trong tương lai

---

## 5. ✅ KẾT LUẬN

### Domain Events:
- **Mục đích:** Event-driven architecture, observability, audit trail
- **Thực tế:** ❌ KHÔNG được sử dụng
- **Kết luận:** ⚠️ **DƯ THỪA** (có thể xóa hoặc giữ lại tùy kế hoạch)

### Domain Layer:
- **Tổng components:** 29
- **Được sử dụng:** 0
- **Kết luận:** ⚠️ **GẦN NHƯ HOÀN TOÀN DƯ THỪA**

### Lý do:
- Application layer hiện tại không phụ thuộc Domain layer
- RAGUseCase đã được refactor để không dùng Domain services
- Code hiện tại tập trung vào tool calling, không cần Domain layer

### Quyết định:
- **Nếu muốn clean code:** Xóa Domain layer (hoặc giữ lại minimal)
- **Nếu muốn giữ cho tương lai:** Giữ lại nhưng document rõ là "for future use"

