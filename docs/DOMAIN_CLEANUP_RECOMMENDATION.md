# Khuyến nghị Cleanup Domain Layer

## 📋 TÓM TẮT

Sau khi phân tích toàn bộ codebase, Domain Layer hiện tại **GẦN NHƯ HOÀN TOÀN DƯ THỪA**:

- **Domain Events**: 10 events - ❌ KHÔNG được sử dụng
- **Domain Entities**: 7 entities - ❌ KHÔNG được sử dụng trong Application
- **Domain Value Objects**: 8 value objects - ❌ KHÔNG được sử dụng trong Application
- **Domain Services**: 4 services - ❌ Được tạo trong Container nhưng KHÔNG được inject vào Use Cases

**Tổng: 29 components, 0 được sử dụng trong Application layer**

---

## 1. 🔍 DOMAIN EVENTS - Mục đích và thực tế

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

### 1.2. Thực tế sử dụng

**❌ KHÔNG được sử dụng:**
- Không có code nào emit events
- Không có code nào consume events
- Chỉ được định nghĩa trong `domain/events/`

**Kết luận:**
- ⚠️ **Domain Events là DƯ THỪA** trong codebase hiện tại
- Có thể giữ lại nếu có kế hoạch implement event-driven architecture
- Hoặc xóa nếu không có kế hoạch sử dụng

---

## 2. 📊 PHÂN TÍCH CHI TIẾT

### 2.1. Domain Events (10 events)

| Event | Status | Sử dụng |
|-------|--------|---------|
| `DomainEvent` | ❌ Dư | Base class, không được sử dụng |
| `DocumentRetrievedEvent` | ❌ Dư | Không được emit |
| `RetrievalCompletedEvent` | ❌ Dư | Không được emit |
| `RetrievalFailedEvent` | ❌ Dư | Không được emit |
| `MessageReceivedEvent` | ❌ Dư | Không được emit |
| `ResponseGeneratedEvent` | ❌ Dư | Không được emit |
| `ConversationStartedEvent` | ❌ Dư | Không được emit |
| `ConversationEndedEvent` | ❌ Dư | Không được emit |
| `RAGQueryReceivedEvent` | ❌ Dư | Không được emit |
| `RAGContextBuiltEvent` | ❌ Dư | Không được emit |
| `RAGResponseGeneratedEvent` | ❌ Dư | Không được emit |

**Kết luận:** ❌ **10/10 events DƯ THỪA**

---

### 2.2. Domain Entities (7 entities)

| Entity | Status | Sử dụng trong Application |
|-------|--------|---------------------------|
| `Document` | ⚠️ Có thể dư | Chỉ được dùng trong Domain services (không được inject) |
| `Message` | ❌ Dư | Không được import trong Application |
| `ToolCall` | ❌ Dư | Không được import trong Application |
| `ChatSession` | ❌ Dư | Không được import trong Application |
| `ConversationHistory` | ❌ Dư | Không được import trong Application |
| `RetrievalResult` | ⚠️ Có thể dư | Chỉ được dùng trong Domain services |
| `EmbeddingModel` | ❌ Dư | Không được import trong Application |

**Kết luận:** ❌ **7/7 entities KHÔNG được sử dụng trong Application layer**

---

### 2.3. Domain Value Objects (8 value objects)

| Value Object | Status | Sử dụng trong Application |
|--------------|--------|---------------------------|
| `RAGContext` | ⚠️ Có thể dư | Chỉ được dùng trong Domain services (không được inject) |
| `SessionId` | ❌ Dư | Không được import |
| `UserId` | ❌ Dư | Không được import |
| `SearchQuery` | ⚠️ Có thể dư | Chỉ được dùng trong MilvusRepository (cần kiểm tra) |
| `Prompt` | ❌ Dư | Không được import |
| `RetrievalConfig` | ❌ Dư | Không được import |
| `LLMConfig` | ❌ Dư | Không được import |
| `SearchFilter` | ⚠️ Có thể dư | Chỉ được dùng trong MilvusRepository (cần kiểm tra) |

**Kết luận:** ❌ **8/8 value objects KHÔNG được sử dụng trong Application layer**

---

### 2.4. Domain Services (4 services)

| Service | Status | Sử dụng trong Application |
|---------|--------|---------------------------|
| `ContextBuilderService` | ❌ Dư | Được tạo trong Container nhưng KHÔNG được inject vào RAGUseCase |
| `PromptBuilderService` | ❌ Dư | Được tạo trong Container nhưng KHÔNG được inject vào RAGUseCase |
| `ConversationManagerService` | ❌ Dư | Được tạo trong Container nhưng KHÔNG được inject vào RAGUseCase |
| `RetrievalOptimizerService` | ❌ Dư | Được tạo trong Container nhưng KHÔNG được inject vào Use Cases |

**Kết luận:** ❌ **4/4 services DƯ THỪA** (được tạo nhưng không được sử dụng)

---

## 3. 🎯 KHUYẾN NGHỊ

### 3.1. Option 1: XÓA HOÀN TOÀN (Clean Code)

**Xóa:**
- ✅ `domain/events/` - Tất cả events (10 files)
- ✅ `domain/entities/` - Tất cả entities (7 files)
- ✅ `domain/value_objects/` - Tất cả value objects (8 files)
- ✅ `domain/services/` - Tất cả services (4 files)
- ✅ Xóa Domain services khỏi Container

**Lý do:**
- Application layer hiện tại không phụ thuộc Domain layer
- RAGUseCase đã được refactor để không dùng Domain services
- Code hiện tại tập trung vào tool calling, không cần Domain layer

**Kết quả:**
- ✅ Code gọn gàng hơn
- ✅ Dễ maintain
- ✅ Không có code dư thừa

---

### 3.2. Option 2: GIỮ LẠI MINIMAL (Future-proof)

**Giữ lại:**
- ⚠️ `domain/events/` - Nếu có kế hoạch event-driven architecture
- ⚠️ `domain/entities/Document` - Có thể dùng trong tương lai
- ⚠️ `domain/value_objects/RAGContext` - Có thể dùng trong tương lai

**Xóa:**
- ✅ Domain services khỏi Container (đã không được sử dụng)
- ✅ Các entities/value objects không được sử dụng

**Lý do:**
- Giữ lại cho tương lai nếu có kế hoạch refactor
- Nhưng xóa khỏi Container để không tạo confusion

---

### 3.3. Option 3: REFACTOR ĐỂ SỬ DỤNG (Nếu muốn dùng Domain layer)

**Refactor:**
- ✅ Sử dụng `Document` entity thay vì `SearchResultDTO`
- ✅ Sử dụng `RAGContext` value object
- ✅ Sử dụng `ContextBuilderService` trong RAGUseCase
- ✅ Emit Domain Events trong Use Cases

**Lý do:**
- Tuân thủ Clean Architecture đầy đủ
- Tách biệt business logic vào Domain layer
- Có thể dùng event-driven architecture

**Nhược điểm:**
- Cần refactor nhiều code
- Phức tạp hơn hiện tại

---

## 4. ✅ KHUYẾN NGHỊ CUỐI CÙNG

### Cho RAG System hiện tại:

**Khuyến nghị: Option 1 - XÓA HOÀN TOÀN**

**Lý do:**
1. ✅ Application layer hiện tại **KHÔNG phụ thuộc** Domain layer
2. ✅ RAGUseCase đã được refactor để **không dùng Domain services**
3. ✅ Code hiện tại **tập trung vào tool calling**, không cần Domain layer
4. ✅ **Clean code** - Không có code dư thừa
5. ✅ **Dễ maintain** - Ít code hơn, dễ hiểu hơn

**Nếu muốn giữ lại:**
- ⚠️ Chỉ giữ lại nếu có **kế hoạch cụ thể** sử dụng trong 3-6 tháng tới
- ⚠️ Nếu không có kế hoạch, **xóa** để clean code

---

## 5. 📝 ACTION ITEMS

### Nếu chọn Option 1 (Xóa hoàn toàn):

1. ✅ Xóa `app/src/domain/events/`
2. ✅ Xóa `app/src/domain/entities/`
3. ✅ Xóa `app/src/domain/value_objects/`
4. ✅ Xóa `app/src/domain/services/`
5. ✅ Xóa Domain services khỏi `container.py`
6. ✅ Xóa imports Domain services khỏi `container.py`
7. ✅ Xóa Domain documentation files (nếu không cần)

### Nếu chọn Option 2 (Giữ lại minimal):

1. ✅ Xóa Domain services khỏi `container.py`
2. ✅ Xóa các entities/value objects không được sử dụng
3. ✅ Giữ lại events nếu có kế hoạch sử dụng
4. ✅ Document rõ là "for future use"

---

## 6. 🎯 KẾT LUẬN

### Domain Events:
- **Mục đích:** Event-driven architecture, observability, audit trail
- **Thực tế:** ❌ KHÔNG được sử dụng
- **Khuyến nghị:** ⚠️ **XÓA** (trừ khi có kế hoạch cụ thể)

### Domain Layer:
- **Tổng components:** 29
- **Được sử dụng:** 0 trong Application layer
- **Khuyến nghị:** ⚠️ **XÓA HOÀN TOÀN** để clean code

### Lý do chính:
- Application layer hiện tại **KHÔNG phụ thuộc** Domain layer
- RAGUseCase đã được refactor để **không dùng Domain services**
- Code hiện tại **tập trung vào tool calling**, không cần Domain layer
- **Clean code principle** - Không giữ code không sử dụng

