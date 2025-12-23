# Mục đích của SearchUseCase và RAGUseCase

## 🎯 TÓM TẮT NHANH

| Use Case | Mục đích | Input | Output | Được dùng bởi |
|----------|----------|-------|--------|---------------|
| **SearchUseCase** | Tìm kiếm documents trong vector store | Query string | Danh sách documents | DocumentController, RAGUseCase (nên dùng) |
| **RAGUseCase** | Chatbot với RAG (Retrieval + Generation) | Câu hỏi của user | Câu trả lời từ LLM | ChatController |

---

## 1. 🔍 SearchUseCase - Mục đích

### Mục đích chính:
**Tìm kiếm documents trong vector store và trả về kết quả**

### Chức năng:
1. **Search documents** - Tìm kiếm documents dựa trên query
2. **Collection auto-detect** - Tự động xác định collection (products vs company_document)
3. **Filter building** - Xây dựng filter expression từ metadata
4. **Multiple search types** - Hỗ trợ vector search, BM25, hybrid search

### Flow:
```
User Query
  → SearchUseCase.search_documents()
    → Determine collection (auto-detect)
    → Build filter expression
    → Call vector_store.hybrid_search()
    → Format results
  → Return SearchResponseDTO (list of documents)
```

### Use cases:
- **API Search**: `/documents/search` - User muốn tìm documents
- **Internal**: Được dùng bởi RAGUseCase để retrieve documents

### Ví dụ sử dụng:
```python
# User muốn tìm documents về "gạch wooden"
search_request = SearchRequestDTO(
    query="gạch wooden",
    top_k=5,
    collection_name=CollectionType.AUTO
)
results = await search_use_case.search_documents(search_request)
# Returns: List of documents matching "gạch wooden"
```

---

## 2. 💬 RAGUseCase - Mục đích

### Mục đích chính:
**Chatbot với RAG - Retrieve documents, build context, generate answer từ LLM**

### Chức năng:
1. **Retrieve** - Tìm documents liên quan (hiện tại tự gọi vector_store)
2. **Build context** - Xây dựng context từ documents
3. **Generate** - Gọi LLM để generate câu trả lời
4. **Cache** - Cache câu trả lời để tăng tốc
5. **Streaming** - Hỗ trợ streaming response qua WebSocket

### Flow:
```
User Question
  → RAGUseCase.process_chat()
    → Check cache
    → Retrieve documents (search)
    → Build context from documents
    → Prepare messages for LLM
    → Call LLM to generate answer
    → Cache response
  → Return ChatResponseDTO (answer + sources)
```

### Use cases:
- **Chat API**: `/chat/completions` - User chat với chatbot
- **WebSocket Chat**: `/chat/ws` - Streaming chat

### Ví dụ sử dụng:
```python
# User hỏi: "Gạch wooden là gì?"
chat_request = ChatRequestDTO(
    question="Gạch wooden là gì?",
    session_id="session_123"
)
response = await rag_use_case.process_chat(chat_request)
# Returns:
# - answer: "Gạch wooden là loại gạch..."
# - sources: [documents used]
# - products: [related products if any]
```

---

## 3. 🔄 SỰ KHÁC BIỆT

### SearchUseCase:
- ✅ **Chỉ tìm kiếm** - Trả về documents
- ✅ **Không có LLM** - Không generate answer
- ✅ **Reusable** - Có thể dùng ở nhiều nơi
- ✅ **Có logic phức tạp** - Auto-detect collection, filter building

### RAGUseCase:
- ✅ **Full RAG flow** - Retrieve + Generate
- ✅ **Có LLM** - Generate answer từ context
- ✅ **Có cache** - Cache responses
- ✅ **Có streaming** - WebSocket support
- ❌ **Hiện tại tự search** - Nên dùng SearchUseCase

---

## 4. 📊 SO SÁNH CHI TIẾT

| Tiêu chí | SearchUseCase | RAGUseCase |
|----------|---------------|------------|
| **Input** | Query string | User question |
| **Output** | List of documents | LLM-generated answer + sources |
| **Dependencies** | vector_store | vector_store, llm_service, cache_service |
| **Collection auto-detect** | ✅ Có | ❌ Không (nên dùng SearchUseCase) |
| **Filter building** | ✅ Có | ❌ Không (nên dùng SearchUseCase) |
| **LLM generation** | ❌ Không | ✅ Có |
| **Caching** | ❌ Không | ✅ Có |
| **Streaming** | ❌ Không | ✅ Có |
| **Reusable** | ✅ Có | ⚠️ Chỉ cho chat |

---

## 5. 🔗 MỐI QUAN HỆ

### Hiện tại (Có vấn đề):
```
RAGUseCase
  └─→ vector_store.hybrid_search()  ❌ Trực tiếp, duplicate logic
```

### Nên là:
```
RAGUseCase
  └─→ SearchUseCase.search_documents()  ✅ Tái sử dụng logic
      └─→ vector_store.hybrid_search()
```

### Lợi ích khi RAGUseCase dùng SearchUseCase:
1. ✅ **Tái sử dụng logic** - Collection auto-detect, filter building
2. ✅ **DRY principle** - Không duplicate code
3. ✅ **Dễ maintain** - Chỉ sửa SearchUseCase khi cần thay đổi search logic
4. ✅ **Consistent** - Cùng logic search cho cả search API và RAG chat

---

## 6. 📝 KẾT LUẬN

### SearchUseCase:
- **Mục đích**: Tìm kiếm documents (pure search functionality)
- **Responsibility**: Search logic, collection detection, filtering
- **Output**: Documents
- **Use case**: Search API, internal search cho RAG

### RAGUseCase:
- **Mục đích**: Chatbot với RAG (Retrieve + Generate)
- **Responsibility**: Orchestrate RAG flow (search → context → LLM → answer)
- **Output**: LLM-generated answer
- **Use case**: Chat API, WebSocket chat

### Quan hệ:
- **SearchUseCase** là **component** của **RAGUseCase**
- RAGUseCase nên **dùng** SearchUseCase thay vì tự implement search
- SearchUseCase có thể **standalone** (search API) hoặc **internal** (cho RAG)

---

## 7. ✅ ĐỀ XUẤT

**RAGUseCase nên refactor để dùng SearchUseCase:**

```python
class RAGUseCase:
    def __init__(
        self,
        search_use_case: SearchUseCase,  # ✅ Thêm
        llm_service: ILLMRepository,
        cache_service: Optional[ISemanticCacheRepository] = None
    ):
        self.search_use_case = search_use_case
        ...

    async def process_chat(self, request: ChatRequestDTO):
        # ✅ Dùng SearchUseCase thay vì vector_store trực tiếp
        search_request = SearchRequestDTO(
            query=request.question,
            top_k=5,
            collection_name=CollectionType.AUTO
        )
        search_response = await self.search_use_case.search_documents(search_request)
        search_results = search_response.results

        # Build context từ search results
        context = self._build_context(search_results)
        ...
```

**Lợi ích**:
- ✅ Có collection auto-detect
- ✅ Có filter expression building
- ✅ Tái sử dụng logic search
- ✅ DRY principle

