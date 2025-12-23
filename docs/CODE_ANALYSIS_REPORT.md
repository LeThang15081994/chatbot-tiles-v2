# Phân tích Code Mới - Báo cáo Chi tiết

## 📋 MỤC ĐÍCH
Phân tích code mới để kiểm tra:
1. Sử dụng LangChain và Langfuse
2. Tích hợp NeMo Guardrails
3. So sánh số phases giữa code cũ và mới
4. Phân tích Domain Layer

---

## 1. 🔍 PHÂN TÍCH LANGCHAIN VÀ LANGFUSE

### 1.1. LangChain - ✅ CÓ SỬ DỤNG

**Vị trí sử dụng:**

#### A. Infrastructure - Milvus Repository
```python
# app/src/infrastructure/milvus/milvus_repository.py
from langchain_milvus import Milvus, BM25BuiltInFunction
from langchain_core.documents import Document as LangchainDocument

class MilvusVectorStoreRepository:
    def __init__(self):
        # LangChain wrappers
        self.langchain_milvus_document: Optional[Milvus] = None
        self.langchain_milvus_products: Optional[Milvus] = None

    def _initialize_langchain_wrappers(self):
        # Initialize LangChain Milvus wrappers
        self.langchain_milvus_document = Milvus(...)
        self.langchain_milvus_products = Milvus(...)
```

**Mục đích**:
- ✅ Wrapper cho Milvus vector store
- ✅ Hỗ trợ hybrid search (vector + BM25)
- ✅ Convert giữa LangChain Document và Domain Document

#### B. Infrastructure - LLM Client
```python
# app/src/infrastructure/llm/litellm_client.py
from langchain_openai import ChatOpenAI

class LiteLLMClient:
    def __init__(self):
        # Initialize LangChain ChatOpenAI with LiteLLM proxy
        self.llm = ChatOpenAI(...)
```

**Mục đích**:
- ✅ Wrapper cho LLM calls qua LiteLLM
- ✅ Hỗ trợ streaming
- ✅ Tool calling support

#### C. Infrastructure - Embedding Service
```python
# app/src/infrastructure/embeddings/embedding_service.py
from langchain_openai import OpenAIEmbeddings

class EmbeddingService:
    def __init__(self):
        # LangChain OpenAI embeddings
        self.embeddings = OpenAIEmbeddings(...)
```

**Mục đích**:
- ✅ Generate embeddings
- ✅ LangChain compatibility

**Kết luận**: ✅ **CÓ sử dụng LangChain** - Chủ yếu trong Infrastructure layer để wrap external services

---

### 1.2. Langfuse - ⚠️ CÓ SERVICE NHƯNG CHƯA TÍCH HỢP ĐẦY ĐỦ

**Vị trí:**

#### A. Infrastructure - LangfuseService
```python
# app/src/infrastructure/observability/langfuse_service.py
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

class LangfuseService:
    def __init__(self):
        self.client: Optional[Langfuse] = None
        self.handler: Optional[CallbackHandler] = None

    def get_callback_handler(self) -> CallbackHandler:
        """Get Langfuse callback handler for LangChain"""
        return self.handler

    def get_session_history(self, session_id: str) -> List[Dict]:
        """Get chat history from Langfuse"""
        # Fetch traces for session
        traces = self.client.api.trace.list(...)
```

**Container:**
```python
# app/src/bootstrap/container.py
langfuse_service = providers.Singleton(
    LangfuseService,
    settings=config.provided.langfuse
)
```

**Vấn đề:**
- ❌ **RAGUseCase KHÔNG sử dụng LangfuseService**
- ❌ **Container inject nhưng không được gọi**
- ❌ **Không có tracing trong RAG flow**
- ⚠️ **Chỉ có comment**: `# This would typically fetch from Langfuse or a database`

**Kết luận**: ⚠️ **CÓ LangfuseService nhưng CHƯA TÍCH HỢP** vào RAGUseCase

---

## 2. 🛡️ PHÂN TÍCH NEMO GUARDRAILS

### 2.1. GuardrailsService - ✅ CÓ SERVICE

**Vị trí:**
```python
# app/src/infrastructure/guardrails/guardrails_service.py
from nemoguardrails import LLMRails, RailsConfig

class GuardrailsService:
    def __init__(self, settings: GuardrailsSettings):
        self.rails: Optional[LLMRails] = None
        self._initialize()

    async def validate_input(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Validate input messages"""
        result = await self.rails.generate_async(
            messages=messages,
            options={"rails": ["input"]}
        )
        # Check if blocked, PII masked, etc.

    async def stream_with_validation(
        self,
        messages: List[Dict[str, str]],
        generator: AsyncGenerator[str, None]
    ) -> AsyncGenerator[str, None]:
        """Stream output with validation"""
        async for chunk in self.rails.stream_async(...):
            if not self._is_guardrails_error(chunk):
                yield chunk
```

**Container:**
```python
# app/src/bootstrap/container.py
guardrails_service = providers.Singleton(
    GuardrailsService,
    settings=config.provided.guardrails
)
```

**Config:**
```yaml
# app/guardrails/config.yml
models:
  - type: main
    engine: openai
    model: "groq"
  - type: self_check_input
    model: "groq-llama-guard"
  - type: self_check_output
    model: "groq-llama-guard"

rails:
  input:
    flows:
      - self check input
  output:
    flows:
      - self check output
```

### 2.2. Vấn đề - ❌ CHƯA TÍCH HỢP VÀO RAGUseCase

**RAGUseCase hiện tại:**
```python
# app/src/application/use_cases/rag_use_case.py
class RAGUseCase:
    def __init__(
        self,
        search_use_case: SearchUseCase,
        llm_service: ILLMRepository,
        cache_service: Optional[ISemanticCacheRepository] = None,
        # ❌ THIẾU: guardrails_service
    ):
        # ...

    async def process_chat(self, request: ChatRequestDTO):
        # ❌ KHÔNG có input validation
        # ❌ KHÔNG có output validation
        # ...
```

**ChatController:**
```python
# app/src/presentation/controllers/chat_controller.py
input_safe=True,  # TODO: Add guardrails integration
output_safe=True,  # TODO: Add guardrails integration
```

**Kết luận**: ❌ **CÓ GuardrailsService nhưng CHƯA TÍCH HỢP** vào RAGUseCase

---

## 3. 📊 SO SÁNH PHASES: CODE CŨ vs CODE MỚI

### 3.1. Code Cũ (Theo tài liệu) - 6 Phases

```
Phase 1: Get Chat History
├─ Fetch from Langfuse API
├─ Format chat history
└─ Limit 12 messages

Phase 2: Guardrails Input Validation
├─ Check input blocking
├─ PII Masking
└─ Alter user input

Phase 3: LLM Generator with Tool Calls
├─ Initial LLM call
├─ Tool detection
├─ Execute tools (search_docs)
├─ Tool message handling
└─ RAG Generation

Phase 4: Guardrails Streaming Output
├─ Stream validation
├─ Check output blocking
└─ Filter unsafe content

Phase 5: Send Products Metadata
├─ Collect product links
├─ Send to frontend
└─ Clear metadata

Phase 6: Done Signal
└─ Send completion
```

**Tổng cộng**: **6 Phases**

---

### 3.2. Code Mới - 3-4 Phases (Đơn giản hơn)

**RAGUseCase.process_chat() (Non-streaming):**
```
Phase 1: Check Cache
└─ Return cached response if available

Phase 2: Search Documents
├─ Extract search parameters
├─ Call SearchUseCase
└─ Convert to Domain Documents

Phase 3: Build Context & Generate
├─ Build context (Domain service)
├─ Build prompt (Domain service)
├─ Call LLM
└─ Cache response

Phase 4: Return Response
└─ Format ChatResponseDTO
```

**RAGUseCase.stream_chat() (Streaming):**
```
Phase 1: Send Metadata
└─ Send session_id, user_id

Phase 2: Check Cache
└─ Return cached if available

Phase 3: Search & Generate
├─ Search documents
├─ Build context
├─ Build prompt
└─ Stream LLM response

Phase 4: Send Products & Done
├─ Send products metadata
└─ Send done signal
```

**Tổng cộng**: **3-4 Phases** (đơn giản hơn code cũ)

---

### 3.3. So sánh

| Feature | Code Cũ | Code Mới | Status |
|---------|---------|----------|--------|
| **Phases** | 6 phases | 3-4 phases | ✅ Đơn giản hơn |
| **Tool Calling** | ✅ Có | ❌ Không có | ❌ Thiếu |
| **Guardrails Input** | ✅ Có | ❌ Không có | ❌ Thiếu |
| **Guardrails Output** | ✅ Có | ❌ Không có | ❌ Thiếu |
| **Langfuse Tracing** | ✅ Có | ❌ Không có | ❌ Thiếu |
| **Chat History** | ✅ Có (Langfuse) | ⚠️ TODO | ⚠️ Chưa có |
| **Conversation Summarization** | ✅ Có | ❌ Không có | ❌ Thiếu |

**Kết luận**:
- ✅ Code mới **đơn giản hơn** (3-4 phases vs 6 phases)
- ❌ Code mới **thiếu nhiều features** (tool calling, guardrails, langfuse)

---

## 4. 🏗️ PHÂN TÍCH DOMAIN LAYER

### 4.1. Cấu trúc Domain Layer

```
domain/
├── entities/           # 7 files
│   ├── chat_session.py
│   ├── message.py
│   ├── document.py
│   ├── tool_call.py
│   ├── retrieval_result.py
│   ├── conversation_history.py
│   └── embedding_model.py
│
├── value_objects/      # 8 files
│   ├── session_id.py
│   ├── user_id.py
│   ├── query.py
│   ├── context.py
│   ├── prompt.py
│   ├── retrieval_config.py
│   ├── llm_config.py
│   └── search_filter.py
│
├── services/           # 4 files
│   ├── context_builder.py
│   ├── prompt_builder.py
│   ├── conversation_manager.py
│   └── retrieval_optimizer.py
│
└── events/             # 4 files
    ├── base_event.py
    ├── retrieval_events.py
    ├── conversation_events.py
    └── rag_events.py
```

**Tổng cộng**: 23 files

---

### 4.2. Kiểm tra Clean Architecture

#### ✅ Đúng - Không phụ thuộc Infrastructure

**Domain entities:**
```python
# domain/entities/document.py
@dataclass
class Document:
    content: str
    document_id: str
    source: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    # ✅ Chỉ dùng Python stdlib (dataclasses, typing, datetime, uuid)
    # ❌ Không có FastAPI, SQLAlchemy, LangChain, etc.
```

**Domain services:**
```python
# domain/services/context_builder.py
from app.src.domain.entities.document import Document
from app.src.domain.value_objects.context import RAGContext

class ContextBuilderService:
    # ✅ Chỉ import từ domain
    # ❌ Không import từ infrastructure
```

#### ✅ Đúng - Rich Domain Model

**Document Entity có behavior:**
```python
class Document:
    def get_score(self, score_type: str = "hybrid") -> Optional[float]:
        """Get relevance score by type"""

    def has_high_relevance(self, threshold: float = 0.7) -> bool:
        """Check if document has high relevance"""

    def format_for_context(self, include_metadata: bool = True) -> str:
        """Format document for LLM context"""
```

**Value Objects immutable:**
```python
@dataclass(frozen=True)
class RAGContext:
    """Immutable value object"""
    documents: tuple
    query: str
    # ...
```

#### ✅ Đúng - Domain Services

**ContextBuilderService:**
- ✅ Pure business logic
- ✅ Không phụ thuộc infrastructure
- ✅ Reusable

**PromptBuilderService:**
- ✅ Pure business logic
- ✅ Template support
- ✅ History integration

---

### 4.3. Vấn đề phát hiện

#### ⚠️ Domain Layer có thể cải thiện

1. **Events không được sử dụng**
   - Domain events được định nghĩa nhưng không được emit/consume
   - Có thể dùng cho event-driven architecture

2. **Một số Value Objects chưa được sử dụng**
   - `RetrievalConfig`, `LLMConfig`, `SearchFilter` - Có thể dùng trong Application layer

3. **ToolCall entity chưa được tích hợp**
   - Entity có sẵn nhưng RAGUseCase không có tool calling

---

### 4.4. Đánh giá tổng thể

| Tiêu chí | Status | Notes |
|----------|--------|-------|
| **Không phụ thuộc Infrastructure** | ✅ | Chỉ dùng Python stdlib |
| **Rich Domain Model** | ✅ | Entities có behavior |
| **Value Objects immutable** | ✅ | @dataclass(frozen=True) |
| **Domain Services pure** | ✅ | Pure business logic |
| **Events defined** | ⚠️ | Có nhưng chưa dùng |
| **Reusable** | ✅ | Có thể dùng ở nhiều nơi |

**Kết luận**: ✅ **Domain Layer viết ĐÚNG** - Tuân thủ Clean Architecture và DDD principles

---

## 5. 📝 TỔNG KẾT

### 5.1. LangChain và Langfuse

| Component | Status | Vị trí | Tích hợp |
|-----------|--------|--------|----------|
| **LangChain** | ✅ Có | Infrastructure | ✅ Được dùng (Milvus, LLM, Embeddings) |
| **Langfuse** | ⚠️ Có service | Infrastructure | ❌ Chưa tích hợp vào RAGUseCase |

### 5.2. NeMo Guardrails

| Component | Status | Vị trí | Tích hợp |
|-----------|--------|--------|----------|
| **GuardrailsService** | ✅ Có | Infrastructure | ❌ Chưa tích hợp vào RAGUseCase |
| **Config** | ✅ Có | `app/guardrails/` | ✅ Đúng cấu hình |

### 5.3. Phases

| Metric | Code Cũ | Code Mới |
|--------|---------|----------|
| **Số phases** | 6 phases | 3-4 phases |
| **Tool Calling** | ✅ Có | ❌ Không có |
| **Guardrails** | ✅ Có | ❌ Không có |
| **Langfuse** | ✅ Có | ❌ Không có |

### 5.4. Domain Layer

| Tiêu chí | Status |
|----------|-------|
| **Clean Architecture** | ✅ Đúng |
| **DDD Principles** | ✅ Đúng |
| **Pure Business Logic** | ✅ Đúng |
| **Reusable** | ✅ Đúng |

---

## 6. ✅ ĐỀ XUẤT

### 6.1. Tích hợp Guardrails vào RAGUseCase

```python
class RAGUseCase:
    def __init__(
        self,
        ...,
        guardrails_service: Optional[GuardrailsService] = None  # ✅ Thêm
    ):
        self.guardrails_service = guardrails_service

    async def process_chat(self, request: ChatRequestDTO):
        # ✅ Input validation
        if self.guardrails_service:
            validation = await self.guardrails_service.validate_input([...])
            if validation["blocked"]:
                raise ValueError("Input blocked by guardrails")

        # ... process ...

        # ✅ Output validation (nếu cần)
```

### 6.2. Tích hợp Langfuse vào RAGUseCase

```python
class RAGUseCase:
    def __init__(
        self,
        ...,
        langfuse_service: Optional[LangfuseService] = None  # ✅ Thêm
    ):
        self.langfuse_service = langfuse_service

    async def process_chat(self, request: ChatRequestDTO):
        # ✅ Start trace
        if self.langfuse_service:
            self.langfuse_service.update_trace(
                session_id=request.session_id,
                user_id=request.user_id
            )

        # ... process ...

        # ✅ Log to Langfuse
```

### 6.3. Thêm Tool Calling (nếu cần)

- Implement tool calling trong LLM client
- Add tool detection phase
- Execute tools before RAG generation

---

## 7. 🎯 KẾT LUẬN

### LangChain & Langfuse:
- ✅ **LangChain**: Có sử dụng trong Infrastructure
- ⚠️ **Langfuse**: Có service nhưng chưa tích hợp

### Guardrails:
- ✅ **Có service và config đúng**
- ❌ **Chưa tích hợp vào RAGUseCase**

### Phases:
- ✅ **Code mới đơn giản hơn** (3-4 vs 6 phases)
- ❌ **Thiếu features** (tool calling, guardrails, langfuse)

### Domain Layer:
- ✅ **Viết ĐÚNG** - Tuân thủ Clean Architecture và DDD

