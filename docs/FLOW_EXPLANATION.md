# Luồng Chạy Hệ Thống (System Flow)

## Tổng Quan

Tài liệu này giải thích chi tiết luồng chạy của hệ thống từ khi user gửi query đến khi nhận được response, bao gồm tất cả các cache layers và embedding calls.

---

## 🚀 Luồng Chính: User Query → Response

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. USER SENDS QUERY (WebSocket)                                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. ChatRouter.websocket_chat()                                   │
│    - Accept WebSocket connection                                 │
│    - Receive JSON message                                        │
│    - Parse WSChatMessageDTO                                      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. ChatController.chat_websocket()                              │
│    - Generate session_id, user_id                                │
│    - Convert to ChatRequestDTO                                   │
│    - Call RAGUseCase.chat_stream()                              │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. RAGUseCase.chat() - PHASE 1: ANSWER CACHE CHECK              │
│    ┌─────────────────────────────────────────────────────────┐  │
│    │ AnswerCache.get(query, namespace="pre-cache")          │  │
│    │   → RedisSemanticCache.lookup()                        │  │
│    │     → ONNXEmbeddings.embed_query(query) [1]           │  │
│    │       → requests.post("/embed")                       │  │
│    │     → Semantic similarity search in Redis             │  │
│    └─────────────────────────────────────────────────────────┘  │
│                                                                   │
│    ✅ CACHE HIT: Return cached answer (SKIP everything below)    │
│    ❌ CACHE MISS: Continue to Phase 2                           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. RAGUseCase.chat() - PHASE 2: LLM CALL WITH TOOLS             │
│    - Load chat history from Langfuse                             │
│    - Summarize history if too long                               │
│    - Build initial messages (PromptBuilder)                      │
│    - Call LLM with tools bound                                   │
│      → llm_service.generate_with_tools()                        │
│        → LiteLLMClient.generate_with_tools()                    │
│          → LLM decides: call tool or answer directly            │
└─────────────────────────────────────────────────────────────────┘
                            ↓
                    ┌───────┴───────┐
                    │               │
        ┌───────────▼──────────┐  ┌─▼──────────────────────┐
        │ LLM calls tool       │  │ LLM answers directly    │
        │ (has_tool_calls=true)│  │ (no tool calls)        │
        └───────────┬──────────┘  └─┬──────────────────────┘
                    │               │
                    └───────┬───────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. RAGUseCase.chat() - PHASE 3: TOOL EXECUTION (if needed)      │
│    For each tool_call:                                          │
│    ┌─────────────────────────────────────────────────────────┐ │
│    │ search_company_info / search_products / etc.            │ │
│    │   → SearchUseCase.search_documents()                   │ │
│    │     → MilvusRepository.hybrid_search()                 │ │
│    │       → wrapper.similarity_search(query)               │ │
│    │         → CachedONNXEmbeddings.embed_query(query) [2]  │ │
│    │           → CacheBackedEmbeddings (check Redis cache) │ │
│    │             ├─> CACHE HIT: Return cached embedding     │ │
│    │             └─> CACHE MISS:                            │ │
│    │                 → ONNXEmbeddings.embed_query(query)    │ │
│    │                   → requests.post("/embed")            │ │
│    │                 → Cache result in Redis                │ │
│    │           → Milvus vector search with embedding        │ │
│    │           → BM25 search (if available)                │ │
│    │           → Combine and score results                  │ │
│    └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. RAGUseCase.chat() - PHASE 4: LLM GENERATION WITH CONTEXT     │
│    - Build context from tool results (ContextBuilder)            │
│    - Build final messages with context                          │
│    - Call LLM for final answer                                  │
│      → llm_service.generate_with_tools()                        │
│        → Streaming response                                     │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 8. RAGUseCase.chat() - PHASE 5: CACHE ANSWER                    │
│    ┌─────────────────────────────────────────────────────────┐  │
│    │ AnswerCache.set(query, answer, namespace)               │  │
│    │   → RedisSemanticCache.update()                         │  │
│    │     → ONNXEmbeddings.embed_query(query) [3]             │  │
│    │       → requests.post("/embed")                        │  │
│    │     → Store: query embedding → answer text             │  │
│    └─────────────────────────────────────────────────────────┘  │
│                                                                   │
│    Namespace:                                                    │
│    - "pre-cache" (20s): No tool calls                           │
│    - "post-cache" (15 min): After tool execution                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 9. ChatController streams response chunks                       │
│    - START message                                              │
│    - SOURCES message (if tool called)                           │
│    - CONTENT chunks (streaming)                                 │
│    - DONE message                                               │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 10. ChatRouter sends to WebSocket client                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Chi Tiết Các Cache Layers

### Layer 1: Answer Cache (Pre-Cache Check)

**Khi nào**: Ngay sau khi nhận query, TRƯỚC khi gọi LLM

**Luồng**:
```
User Query
  → AnswerCache.get(query, namespace="pre-cache")
    → RedisSemanticCache.lookup(query)
      → ONNXEmbeddings.embed_query(query)  [Embedding call #1]
        → requests.post("http://localhost:7000/embed")
      → Semantic similarity search trong Redis
        → Tìm cached answer tương tự
    → Return cached answer nếu tìm thấy
```

**Kết quả**:
- ✅ **HIT**: Return ngay, SKIP tất cả (LLM, tools, embedding, Milvus)
- ❌ **MISS**: Continue to Phase 2

**TTL**: 20 giây

---

### Layer 2: Embedding Cache (Trong Tool Execution)

**Khi nào**: Khi tool được gọi và cần embedding cho vector search

**Luồng**:
```
Tool Call (search_company_info, search_products, etc.)
  → SearchUseCase.search_documents()
    → MilvusRepository.hybrid_search()
      → wrapper.similarity_search(query)
        → CachedONNXEmbeddings.embed_query(query)  [Embedding call #2]
          → CacheBackedEmbeddings.embed_query()
            → Check Redis cache (key: text + embedding_version)
              ├─> ✅ CACHE HIT: Return cached embedding
              └─> ❌ CACHE MISS:
                  → ONNXEmbeddings.embed_query(query)
                    → requests.post("http://localhost:7000/embed")
                  → Cache result in Redis
          → Milvus vector search với embedding
          → BM25 search (nếu có)
          → Combine results
```

**Kết quả**:
- ✅ **HIT**: Không gọi `/embed`, dùng cached embedding
- ❌ **MISS**: Gọi `/embed`, cache kết quả

**TTL**: 1 giờ

---

### Layer 3: Context Cache (Optional - Chưa tích hợp)

**Khi nào**: Nếu sử dụng `CachedRetriever` (hiện chưa dùng)

**Luồng**:
```
CachedRetriever.invoke(query)
  → ContextCache.get(query, k, collection, filters)
    → Check Redis cache (key: query_hash + config_hash)
      ├─> ✅ CACHE HIT: Return cached documents
      │     → SKIP retriever, SKIP embedding, SKIP Milvus
      └─> ❌ CACHE MISS:
          → Retriever.invoke(query)
            → CachedONNXEmbeddings.embed_query() [Embedding call]
            → Milvus similarity search
          → ContextCache.set(query, documents)
```

**Kết quả**:
- ✅ **HIT**: Skip toàn bộ retriever execution
- ❌ **MISS**: Execute retriever, cache result

**TTL**: 1 giờ

**Note**: Hiện chưa được tích hợp vào pipeline, có thể dùng trong tương lai.

---

### Layer 4: Answer Cache (Post-Cache Store)

**Khi nào**: Sau khi LLM generate answer

**Luồng**:
```
LLM generates answer
  → AnswerCache.set(query, answer, namespace)
    → RedisSemanticCache.update(query, answer)
      → ONNXEmbeddings.embed_query(query)  [Embedding call #3]
        → requests.post("http://localhost:7000/embed")
      → Store: query embedding → answer text trong Redis
```

**Namespace**:
- `"pre-cache"` (20s): Nếu không có tool calls
- `"post-cache"` (15 min): Nếu có tool calls

---

## 🔢 Số Lần Embedding Call

### Scenario 1: Answer Cache HIT (Best Case)
```
Embedding calls: 1
- AnswerCache.get() → embed_query(query) để tìm semantic match
- ✅ Return cached answer, SKIP tất cả
```

### Scenario 2: Answer Cache MISS, Tool Called, Embedding Cache HIT
```
Embedding calls: 2
1. AnswerCache.get() → embed_query(query) [MISS, không tìm thấy]
2. Tool execution → CachedONNXEmbeddings.embed_query(query) [CACHE HIT, dùng cached]
3. AnswerCache.set() → embed_query(query) [để cache answer]
```

### Scenario 3: Answer Cache MISS, Tool Called, Embedding Cache MISS
```
Embedding calls: 3
1. AnswerCache.get() → embed_query(query) [MISS]
2. Tool execution → CachedONNXEmbeddings.embed_query(query) [CACHE MISS, gọi /embed]
3. AnswerCache.set() → embed_query(query) [để cache answer]
```

### Scenario 4: Answer Cache MISS, No Tool Calls
```
Embedding calls: 2
1. AnswerCache.get() → embed_query(query) [MISS]
2. AnswerCache.set() → embed_query(query) [để cache answer]
```

---

## 🎯 Điểm Quan Trọng

### 1. Embedding Chỉ Được Gọi Ở 3 Nơi

1. **AnswerCache.get()**: Để tìm semantic match trong cached answers
2. **CachedONNXEmbeddings.embed_query()**: Khi tool cần vector search
3. **AnswerCache.set()**: Để cache answer với query embedding

### 2. Không Có Manual Embedding Calls

- ✅ Không có `embed_query()` trong business logic
- ✅ Embedding chỉ được trigger bởi:
  - `AnswerCache` (semantic cache)
  - `CachedONNXEmbeddings` (via Milvus wrapper)

### 3. Cache Layers Hoạt Động Độc Lập

- **AnswerCache**: Cache LLM responses (answers)
- **CachedONNXEmbeddings**: Cache embedding vectors
- **ContextCache**: Cache retriever results (chưa dùng)

Mỗi layer có mục đích riêng và không conflict với nhau.

### 4. Luồng Async/Streaming

- Tất cả operations đều async
- LLM response được stream về client
- Cache operations không block streaming

---

## 📝 Ví Dụ Cụ Thể

### Example 1: Query "What is your company history?"

```
1. AnswerCache.get("What is your company history?", "pre-cache")
   → embed_query() → /embed → Semantic search → ❌ MISS

2. LLM decides: call search_company_info tool

3. Tool execution:
   → MilvusRepository.hybrid_search("What is your company history?")
     → CachedONNXEmbeddings.embed_query("What is your company history?")
       → CacheBackedEmbeddings check → ❌ MISS
         → ONNXEmbeddings.embed_query() → /embed
         → Cache embedding in Redis
     → Milvus vector search
     → Return documents

4. LLM generates answer with context

5. AnswerCache.set("What is your company history?", answer, "post-cache")
   → embed_query() → /embed → Store in Redis

Total embedding calls: 3
```

### Example 2: Same Query Again (Within 20 seconds)

```
1. AnswerCache.get("What is your company history?", "pre-cache")
   → embed_query() → /embed → Semantic search → ✅ HIT
   → Return cached answer

Total embedding calls: 1
SKIP: Tool execution, Milvus, LLM generation
```

### Example 3: Similar Query "Tell me about your company"

```
1. AnswerCache.get("Tell me about your company", "pre-cache")
   → embed_query() → /embed → Semantic search → ✅ HIT (similar to cached)
   → Return cached answer from "What is your company history?"

Total embedding calls: 1
SKIP: Tool execution, Milvus, LLM generation
```

---

## 🔄 Tóm Tắt Luồng

1. **User Query** → WebSocket
2. **Answer Cache Check** → Nếu HIT, return ngay
3. **LLM Call** → Quyết định có cần tool không
4. **Tool Execution** (nếu cần):
   - Embedding (có cache check)
   - Milvus search
   - Return documents
5. **LLM Generation** → Với context từ tools
6. **Cache Answer** → Store trong AnswerCache
7. **Stream Response** → Về client

**Key Point**: Embedding chỉ được gọi khi thực sự cần, và được cache để tránh duplicate calls.

