# So sánh Cơ chế Search: Code Mới vs Code Cũ

## 📋 KẾT LUẬN

### ❌ Code Mới KHÔNG có Tool Search
### ✅ Code Mới search theo cơ chế **Direct Search** (luôn search trước)
### ❌ KHÔNG giống code cũ (code cũ có Tool Calling, LLM quyết định)

---

## 1. 🔍 CODE MỚI - Cơ chế Search hiện tại

### 1.1. Cơ chế: **Direct Search** (Luôn search trước)

**Flow:**
```
User Question
  ↓
RAGUseCase.process_chat() hoặc stream_chat()
  ↓
[Guardrails Input Validation]
  ↓
[Check Cache]
  ↓
🔍 **TỰ ĐỘNG SEARCH** (Luôn luôn)
  ├─ Extract search parameters từ request.metadata
  ├─ Call SearchUseCase.search_documents()
  └─ Convert SearchResultDTO → Domain Documents
  ↓
Build Context (ContextBuilderService)
  ↓
Build Prompt (PromptBuilderService)
  ↓
Generate Response (LLM)
  ↓
[Guardrails Output Validation]
  ↓
Return Response
```

**Code thực tế:**
```python
# app/src/application/use_cases/rag_use_case.py

async def process_chat(self, request: ChatRequestDTO):
    # ... Guardrails input validation ...
    # ... Check cache ...

    # 🔍 TỰ ĐỘNG SEARCH - Luôn luôn search
    search_request = SearchRequestDTO(
        query=request.question,
        top_k=top_k,
        collection_name=collection_type,
        metadata_filter=metadata_filter
    )

    search_response = await self.search_use_case.search_documents(search_request)
    search_results = search_response.results

    # Convert to Domain Documents
    domain_documents = self._convert_to_domain_documents(search_results)

    # Build context và generate
    # ...
```

**Đặc điểm:**
- ✅ **Luôn search** - Không có điều kiện
- ✅ **Search trước khi generate** - Không có tool calling
- ✅ **LLM không quyết định** - Search được thực hiện tự động
- ✅ **Đơn giản** - Không có multi-phase

---

### 1.2. SearchUseCase

**Vị trí:** `app/src/application/use_cases/search_use_case.py`

**Chức năng:**
```python
class SearchUseCase:
    async def search_documents(
        self,
        request: SearchRequestDTO
    ) -> SearchResponseDTO:
        # Determine collection name
        # Build filter expression
        # Execute hybrid search
        # Return results
```

**Được gọi từ:**
- ✅ `RAGUseCase.process_chat()` - Direct call
- ✅ `RAGUseCase.stream_chat()` - Direct call
- ✅ `DocumentController.search_documents()` - API endpoint

---

## 2. 🔧 CODE CŨ - Cơ chế Search (Theo tài liệu)

### 2.1. Cơ chế: **Tool Calling** (LLM quyết định)

**Flow:**
```
User Question
  ↓
Phase 1: Get Chat History (Langfuse)
  ↓
Phase 2: Guardrails Input Validation
  ↓
Phase 3: LLM Generator with Tool Calls
  ├─ Initial LLM call (với tools bound)
  ├─ 🔍 **LLM QUYẾT ĐỊNH** có cần search không
  ├─ Nếu LLM gọi tool search_docs:
  │   ├─ Extract tool arguments
  │   ├─ Execute search_docs tool
  │   └─ Return tool result
  ├─ Tool message handling
  └─ RAG Generation (với context từ tool)
  ↓
Phase 4: Guardrails Streaming Output
  ↓
Phase 5: Send Products Metadata
  ↓
Phase 6: Done Signal
```

**Code cũ (theo tài liệu):**
```python
# chat-backend/src/services/application/rag.py

# 1. Define SearchArgs
class SearchArgs(BaseModel):
    query: str
    top_k: int = 5
    collection_name: Optional[str] = None

# 2. Create search_tool
search_tool = StructuredTool.from_function(
    func=search_docs,
    name="search_docs",
    description="Search documents in the knowledge base",
    args_schema=SearchArgs
)

# 3. Bind tools to LLM
llm_with_tools = llm.bind_tools([search_tool])

# 4. Initial LLM call (detect tools)
response = await llm_with_tools.ainvoke(messages)

# 5. Check for tool calls
if response.tool_calls:
    # Execute tools
    for tool_call in response.tool_calls:
        if tool_call["name"] == "search_docs":
            # Execute search
            results = await search_docs(**tool_call["args"])
            # Add tool message
            messages.append({
                "role": "tool",
                "content": results,
                "tool_call_id": tool_call["id"]
            })

    # 6. RAG Generation với context từ tool
    final_response = await llm_with_tools.ainvoke(messages)
```

**Đặc điểm:**
- ✅ **LLM quyết định** - LLM tự quyết định khi nào cần search
- ✅ **Tool calling** - Sử dụng StructuredTool
- ✅ **Multi-phase** - Initial call → Tool execution → RAG generation
- ✅ **Linh hoạt** - LLM có thể không search nếu không cần

---

## 3. 📊 SO SÁNH CHI TIẾT

| Tiêu chí | Code Mới | Code Cũ |
|----------|----------|---------|
| **Cơ chế** | Direct Search | Tool Calling |
| **Khi nào search?** | Luôn luôn (tự động) | LLM quyết định |
| **Tool search?** | ❌ Không có | ✅ Có (StructuredTool) |
| **Multi-phase?** | ❌ Không (single phase) | ✅ Có (3 phases) |
| **LLM quyết định?** | ❌ Không | ✅ Có |
| **Search trước generate?** | ✅ Luôn luôn | ⚠️ Có thể (nếu LLM gọi tool) |
| **Độ phức tạp** | ✅ Đơn giản | ⚠️ Phức tạp hơn |
| **Linh hoạt** | ⚠️ Ít linh hoạt | ✅ Linh hoạt hơn |

---

## 4. 🎯 ƯU VÀ NHƯỢC ĐIỂM

### 4.1. Code Mới (Direct Search)

**Ưu điểm:**
- ✅ **Đơn giản** - Dễ hiểu, dễ maintain
- ✅ **Predictable** - Luôn search, không phụ thuộc LLM
- ✅ **Nhanh hơn** - Không cần initial LLM call để detect tools
- ✅ **Ít token** - Không cần tool calling overhead

**Nhược điểm:**
- ❌ **Không linh hoạt** - Luôn search dù có thể không cần
- ❌ **Tốn tài nguyên** - Search ngay cả khi câu hỏi không cần knowledge base
- ❌ **Không thông minh** - LLM không thể quyết định khi nào cần search

**Ví dụ không tối ưu:**
```python
# User: "Hello, how are you?"
# → Code mới vẫn search documents (không cần thiết)
# → Tốn thời gian và tài nguyên
```

---

### 4.2. Code Cũ (Tool Calling)

**Ưu điểm:**
- ✅ **Thông minh** - LLM quyết định khi nào cần search
- ✅ **Linh hoạt** - Có thể không search nếu không cần
- ✅ **Tiết kiệm** - Chỉ search khi thực sự cần
- ✅ **Agent-like** - LLM có thể quyết định strategy

**Nhược điểm:**
- ❌ **Phức tạp** - Multi-phase, nhiều logic
- ❌ **Chậm hơn** - Cần initial LLM call để detect tools
- ❌ **Tốn token** - Tool calling overhead
- ❌ **Khó debug** - Nhiều phases, khó trace

**Ví dụ tối ưu:**
```python
# User: "Hello, how are you?"
# → LLM quyết định KHÔNG cần search
# → Trả lời trực tiếp (tiết kiệm)

# User: "What is wooden tile?"
# → LLM quyết định CẦN search
# → Gọi tool search_docs
# → Generate với context
```

---

## 5. 🔄 KẾT LUẬN

### Code Mới:
- ❌ **KHÔNG có tool search**
- ✅ **Search theo cơ chế Direct Search** (luôn search trước)
- ❌ **KHÔNG giống code cũ**

### Code Cũ:
- ✅ **Có tool search** (StructuredTool)
- ✅ **Search theo cơ chế Tool Calling** (LLM quyết định)
- ✅ **Multi-phase flow**

### Khuyến nghị:
- **Nếu muốn giống code cũ**: Cần implement tool calling
- **Nếu muốn đơn giản**: Giữ nguyên direct search (nhưng kém linh hoạt)

---

## 6. 📝 CODE MỚI CẦN BỔ SUNG ĐỂ GIỐNG CODE CŨ

### 6.1. Tạo Search Tool
```python
# app/src/application/tools/search_tool.py
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

class SearchArgs(BaseModel):
    query: str = Field(..., description="Search query")
    top_k: int = Field(5, description="Number of results")
    collection_name: Optional[str] = Field(None, description="Collection name")

def create_search_tool(search_use_case: SearchUseCase):
    async def search_docs(query: str, top_k: int = 5, collection_name: Optional[str] = None):
        """Search documents in knowledge base"""
        request = SearchRequestDTO(
            query=query,
            top_k=top_k,
            collection_name=collection_name or CollectionType.AUTO
        )
        response = await search_use_case.search_documents(request)
        return response.results

    return StructuredTool.from_function(
        func=search_docs,
        name="search_docs",
        description="Search documents in the knowledge base about ceramic tiles",
        args_schema=SearchArgs
    )
```

### 6.2. Multi-phase Flow trong RAGUseCase
```python
# Phase 1: Initial LLM call với tools
response = await llm_service.generate_with_tools(
    messages=messages,
    tools=[search_tool]
)

# Phase 2: Execute tools nếu có
if response.tool_calls:
    for tool_call in response.tool_calls:
        if tool_call["name"] == "search_docs":
            results = await execute_search_tool(tool_call)
            messages.append({
                "role": "tool",
                "content": results,
                "tool_call_id": tool_call["id"]
            })

# Phase 3: RAG Generation với context từ tools
final_response = await llm_service.generate_response(messages)
```

---

## 7. ✅ TÓM TẮT

| Câu hỏi | Trả lời |
|---------|---------|
| **Code mới có tool search không?** | ❌ KHÔNG |
| **Code mới search theo cơ chế nào?** | ✅ **Direct Search** (luôn search trước) |
| **Có giống code cũ không?** | ❌ KHÔNG (code cũ có Tool Calling) |

**Code mới:**
- Search tự động, luôn luôn
- Không có tool calling
- Đơn giản nhưng kém linh hoạt

**Code cũ:**
- LLM quyết định khi nào search
- Có tool calling
- Phức tạp nhưng linh hoạt hơn

