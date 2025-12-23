# Phân tích Application/ và Domain/ Layers

## 🔍 1. TRÙNG LẶP GIỮA APPLICATION/ VÀ DOMAIN/

### ❌ Vấn đề phát hiện:

#### 1.1. Context Building Logic - TRÙNG LẶP
**Location:**
- `app/src/application/use_cases/rag_use_case.py` - method `_build_context()` (lines 240-271)
- `app/src/domain/services/context_builder.py` - class `ContextBuilderService`

**Vấn đề:**
- `RAGUseCase._build_context()` tự implement logic build context từ search results
- `ContextBuilderService.build_context()` đã có sẵn logic tương tự nhưng tốt hơn (có sorting, formatting, metadata handling)
- Container đã inject `context_builder` vào `RAGUseCase` nhưng không được sử dụng

**Code hiện tại:**
```python
# RAGUseCase._build_context() - Đơn giản, thiếu features
def _build_context(self, search_results: List[Any]) -> str:
    context_parts = []
    for idx, result in enumerate(search_results, 1):
        context_parts.append(f"[Document {idx}]")
        context_parts.append(result.content)
    return "\n\n".join(context_parts)
```

**Code domain service (tốt hơn):**
```python
# ContextBuilderService - Có sorting, metadata, scores, truncation
def build_context(self, documents: List[Document], query: str) -> RAGContext:
    sorted_docs = self._sort_by_relevance(documents)
    context_text = self._format_documents(sorted_docs)
    return RAGContext.from_documents(...)
```

#### 1.2. Prompt Building Logic - TRÙNG LẶP
**Location:**
- `app/src/application/use_cases/rag_use_case.py` - method `_prepare_messages()` (lines 273-313)
- `app/src/domain/services/prompt_builder.py` - class `PromptBuilderService`

**Vấn đề:**
- `RAGUseCase._prepare_messages()` tự build prompt đơn giản
- `PromptBuilderService.build_rag_prompt()` có đầy đủ features (history, templates, formatting)
- Container đã inject `prompt_builder` nhưng không được sử dụng

**Code hiện tại:**
```python
# RAGUseCase._prepare_messages() - Đơn giản
def _prepare_messages(self, question: str, context: str, session_id: Optional[str] = None):
    system_prompt = """You are a helpful assistant..."""
    if context:
        system_prompt += f"\n\nContext:\n{context}"
    messages.append(ChatMessageDTO(role="system", content=system_prompt))
    messages.append(ChatMessageDTO(role="user", content=question))
    return messages
```

**Code domain service (tốt hơn):**
```python
# PromptBuilderService - Có history, templates, formatting
def build_rag_prompt(self, query: str, context: RAGContext, chat_history: Optional[List[Message]] = None):
    # Có xử lý history, templates, formatting tốt hơn
```

#### 1.3. Conversation Management - THIẾU TÍCH HỢP
**Location:**
- `app/src/application/use_cases/rag_use_case.py` - method `get_chat_history()` (lines 215-238)
- `app/src/domain/services/conversation_manager.py` - class `ConversationManagerService`

**Vấn đề:**
- `RAGUseCase.get_chat_history()` chỉ return empty (TODO)
- `ConversationManagerService` có đầy đủ logic quản lý conversation nhưng không được sử dụng
- Container đã inject `conversation_manager` nhưng không được sử dụng

---

## 🔄 2. SO SÁNH VỚI CODE CŨ (chat-backend)

### 2.1. Chức năng có trong code cũ nhưng THIẾU trong code mới:

#### ❌ Tool Calling với Search Tool
**Code cũ:**
- `chat-backend/src/services/application/rag.py` có `SearchArgs` Pydantic model
- Có `search_tool = StructuredTool.from_function(...)`
- LLM có thể gọi tool `search_docs` để tìm kiếm documents
- Có `WebSocketGeneratorService` xử lý tool calling flow

**Code mới:**
- `RAGUseCase` không có tool calling
- Không có search tool integration
- LLM không thể tự động quyết định khi nào cần search

#### ❌ WebSocket Streaming với Tool Execution
**Code cũ:**
- `WebSocketGeneratorService` có 3 phases:
  1. Initial LLM call (detect tools)
  2. Tool execution (search_docs)
  3. RAG generation (với context từ tools)

**Code mới:**
- `RAGUseCase.stream_chat()` chỉ có simple streaming
- Không có tool detection và execution
- Không có multi-phase generation

#### ❌ Conversation Summarization
**Code cũ:**
- `SummarizeService` có `_summarize_and_truncate_history()`
- Tự động summarize old messages khi history quá dài
- Tích hợp với Langfuse

**Code mới:**
- `ConversationManagerService` có logic summarization nhưng không được tích hợp
- `RAGUseCase` không sử dụng summarization

#### ❌ Langfuse Integration đầy đủ
**Code cũ:**
- Langfuse tracing cho từng phase (initial call, tool execution, RAG generation)
- Session và user tracking
- Token usage tracking

**Code mới:**
- Có `LangfuseService` nhưng integration chưa đầy đủ trong RAG flow

#### ❌ Guardrails Integration trong RAG Flow
**Code cũ:**
- Guardrails được tích hợp trong `get_ws_response()`:
  - Input validation trước khi process
  - Output validation trong streaming
  - PII masking

**Code mới:**
- Có `GuardrailsService` nhưng `RAGUseCase` không sử dụng
- Container inject nhưng không được gọi

---

## 📊 3. TỔNG KẾT VẤN ĐỀ

### 3.1. Trùng lặp code:
1. ✅ `_build_context()` → Nên dùng `ContextBuilderService`
2. ✅ `_prepare_messages()` → Nên dùng `PromptBuilderService`
3. ✅ `get_chat_history()` → Nên dùng `ConversationManagerService`

### 3.2. Thiếu chức năng:
1. ❌ Tool calling (search_docs tool)
2. ❌ Multi-phase WebSocket streaming (tool detection → execution → RAG)
3. ❌ Conversation summarization integration
4. ❌ Guardrails integration trong RAG flow
5. ❌ Langfuse tracing đầy đủ

### 3.3. Domain services không được sử dụng:
- `ContextBuilderService` - Đã inject nhưng không dùng
- `PromptBuilderService` - Đã inject nhưng không dùng
- `ConversationManagerService` - Đã inject nhưng không dùng
- `RetrievalOptimizerService` - Đã inject nhưng không dùng

---

## ✅ 4. ĐỀ XUẤT REFACTOR

### 4.1. Refactor RAGUseCase để sử dụng Domain Services:

```python
class RAGUseCase:
    def __init__(
        self,
        vector_store: IVectorStoreRepository,
        llm_service: ILLMRepository,
        cache_service: Optional[ISemanticCacheRepository] = None,
        context_builder: ContextBuilderService,  # ✅ Sử dụng
        prompt_builder: PromptBuilderService,    # ✅ Sử dụng
        conversation_manager: ConversationManagerService,  # ✅ Sử dụng
        guardrails_service: GuardrailsService,   # ✅ Sử dụng
        langfuse_service: LangfuseService,       # ✅ Sử dụng
    ):
        # ...

    async def process_chat(self, request: ChatRequestDTO) -> ChatResponseDTO:
        # 1. Validate input với guardrails
        validation = await self.guardrails_service.validate_input(...)
        if validation["blocked"]:
            return error_response

        # 2. Get conversation history
        history = await self.conversation_manager.get_history(request.session_id)

        # 3. Retrieve documents
        search_results = await self.vector_store.hybrid_search(...)

        # 4. Build context với ContextBuilderService
        context = self.context_builder.build_context(
            documents=search_results,
            query=request.question
        )

        # 5. Build prompt với PromptBuilderService
        prompt = self.prompt_builder.build_rag_prompt(
            query=request.question,
            context=context,
            chat_history=history
        )

        # 6. Generate response
        answer = await self.llm_service.generate_response(...)

        # 7. Validate output với guardrails
        # ...

        return response
```

### 4.2. Thêm Tool Calling:

Cần thêm:
- `ToolCallingService` trong domain hoặc infrastructure
- `SearchTool` implementation
- Integration với LLM để bind tools
- Multi-phase streaming flow

### 4.3. Thêm Summarization Integration:

```python
# Trong RAGUseCase
if self.conversation_manager.should_summarize(history):
    summary = await self.summarize_service.summarize(...)
    history = self.conversation_manager.apply_summary(history, summary)
```

---

## 🎯 5. KẾT LUẬN

**Vấn đề chính:**
1. ❌ Code trùng lặp giữa Application và Domain layers
2. ❌ Domain services được tạo và inject nhưng không được sử dụng
3. ❌ Thiếu nhiều chức năng quan trọng từ code cũ

**Hành động cần thiết:**
1. ✅ Refactor `RAGUseCase` để sử dụng domain services
2. ✅ Xóa duplicate code (`_build_context`, `_prepare_messages`)
3. ✅ Thêm tool calling functionality
4. ✅ Tích hợp guardrails vào RAG flow
5. ✅ Tích hợp summarization
6. ✅ Cải thiện Langfuse tracing

