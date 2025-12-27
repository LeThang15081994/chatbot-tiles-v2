# Luồng Chạy Hệ Thống - Diagram Đơn Giản

## 🎯 Luồng Tổng Quan

```
┌─────────────────────────────────────────────────────────────┐
│                    USER QUERY                                │
│              (WebSocket / REST API)                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: ANSWER CACHE CHECK (Pre-Cache)                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ AnswerCache.get(query, "pre-cache")                  │  │
│  │   → embed_query(query) [1] → /embed                 │  │
│  │   → Semantic search in Redis                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ✅ HIT: Return cached answer → END                        │
│  ❌ MISS: Continue                                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: LLM CALL WITH TOOLS                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ - Load chat history                                   │  │
│  │ - Build messages                                      │  │
│  │ - Call LLM with tools bound                           │  │
│  │   → LLM decides: call tool or answer directly        │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
            ┌──────────┴──────────┐
            │                     │
    ┌───────▼────────┐   ┌────────▼──────────┐
    │ LLM calls tool │   │ LLM answers       │
    │                │   │ directly         │
    └───────┬────────┘   └────────┬──────────┘
            │                     │
            └──────────┬──────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: TOOL EXECUTION (if tool called)                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ search_company_info / search_products / etc.        │  │
│  │   → SearchUseCase.search_documents()                │  │
│  │     → MilvusRepository.hybrid_search()             │  │
│  │       → wrapper.similarity_search(query)            │  │
│  │         → CachedONNXEmbeddings.embed_query() [2]   │  │
│  │           → CacheBackedEmbeddings                   │  │
│  │             ├─> ✅ HIT: Use cached embedding        │  │
│  │             └─> ❌ MISS:                           │  │
│  │                 → ONNXEmbeddings.embed_query()      │  │
│  │                   → /embed                         │  │
│  │                 → Cache in Redis                    │  │
│  │           → Milvus vector search                   │  │
│  │           → BM25 search (if available)              │  │
│  │           → Return documents                        │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 4: LLM GENERATION WITH CONTEXT                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ - Build context from tool results                    │  │
│  │ - Build final messages                               │  │
│  │ - Call LLM for final answer                          │  │
│  │   → Streaming response                               │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 5: CACHE ANSWER                                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ AnswerCache.set(query, answer, namespace)            │  │
│  │   → embed_query(query) [3] → /embed                 │  │
│  │   → Store in Redis                                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  Namespace:                                                  │
│  - "pre-cache" (20s): No tool calls                         │
│  - "post-cache" (15 min): After tool execution              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 6: STREAM RESPONSE TO CLIENT                          │
│  - START → SOURCES → CONTENT chunks → DONE                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Cache Layers

### Layer 1: Answer Cache (Pre-Cache)
```
Query → AnswerCache.get() → embed_query() → Semantic search → Cached answer?
```
- **TTL**: 20 giây
- **Mục đích**: Tránh gọi LLM cho queries tương tự
- **Embedding call**: Có (để semantic search)

### Layer 2: Embedding Cache
```
Query → CachedONNXEmbeddings.embed_query() → CacheBackedEmbeddings → Redis cache → Cached embedding?
```
- **TTL**: 1 giờ
- **Mục đích**: Tránh gọi `/embed` cho cùng một text
- **Embedding call**: Chỉ khi cache MISS

### Layer 3: Context Cache (Optional - Chưa dùng)
```
Query → ContextCache.get() → Cached documents?
```
- **TTL**: 1 giờ
- **Mục đích**: Tránh duplicate retriever execution
- **Embedding call**: Không (cache documents, không phải embeddings)

### Layer 4: Answer Cache (Post-Cache)
```
Query + Answer → AnswerCache.set() → embed_query() → Store in Redis
```
- **TTL**: 20s (pre-cache) hoặc 15 min (post-cache)
- **Mục đích**: Cache LLM responses
- **Embedding call**: Có (để semantic search sau này)

---

## 🔢 Số Lần Embedding Call

### Best Case: Answer Cache HIT
```
Embedding calls: 1
- AnswerCache.get() → embed_query(query)
- ✅ Return cached answer
```

### Normal Case: Tool Called, Embedding Cache HIT
```
Embedding calls: 2
1. AnswerCache.get() → embed_query(query) [MISS]
2. Tool → CachedONNXEmbeddings.embed_query(query) [CACHE HIT]
3. AnswerCache.set() → embed_query(query)
```

### Worst Case: Tool Called, Embedding Cache MISS
```
Embedding calls: 3
1. AnswerCache.get() → embed_query(query) [MISS]
2. Tool → CachedONNXEmbeddings.embed_query(query) [CACHE MISS → /embed]
3. AnswerCache.set() → embed_query(query)
```

---

## 🎯 Điểm Quan Trọng

1. **Embedding chỉ được gọi ở 3 nơi**:
   - AnswerCache.get() - Tìm semantic match
   - CachedONNXEmbeddings.embed_query() - Vector search
   - AnswerCache.set() - Cache answer

2. **Không có manual embedding calls** trong business logic

3. **Cache layers hoạt động độc lập**, không conflict

4. **Luồng async/streaming** - không block

