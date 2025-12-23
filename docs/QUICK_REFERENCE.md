# Domain Layer - Quick Reference

## 🚀 Quick Start

### Import Everything
```python
from src.domain import (
    # Entities
    ChatSession, Message, MessageRole, Document,
    ToolCall, ToolResult, RetrievalResult,
    ConversationHistory, EmbeddingModel,

    # Value Objects
    SessionId, UserId, SearchQuery, RAGContext,
    PromptTemplate, RetrievalConfig, LLMConfig,
    SearchFilter,

    # Services
    ContextBuilderService, PromptBuilderService,
    ConversationManagerService, RetrievalOptimizerService,

    # Events
    DocumentRetrievedEvent, ResponseGeneratedEvent,
    RAGQueryReceivedEvent
)
```

---

## 📦 Entities Cheat Sheet

### ChatSession
```python
# Create session
session = ChatSession(user_id="user123")

# Add message
message = Message(content="Hello", role=MessageRole.USER)
session.add_message(message)

# Get recent messages
recent = session.get_recent_messages(count=10)

# Clear old messages
removed = session.clear_old_messages(keep_count=10)
```

### Document
```python
# Create document
doc = Document(
    content="RAG is...",
    source="docs/rag.md",
    hybrid_score=0.95,
    metadata={"category": "technical"}
)

# Check relevance
if doc.has_high_relevance(threshold=0.7):
    print("Highly relevant!")

# Format for context
formatted = doc.format_for_context(include_metadata=True)
```

### RetrievalResult
```python
# Create result
result = RetrievalResult(
    query="What is RAG?",
    documents=[doc1, doc2, doc3],
    strategy=RetrievalStrategy.HYBRID
)

# Get statistics
avg_score = result.get_average_score()
top_3 = result.get_top_k(k=3)
sources = result.get_unique_sources()

# Check quality
is_good = result.is_high_quality(min_docs=3, min_avg_score=0.6)
```

### ConversationHistory
```python
# Create history
history = ConversationHistory(session_id="session123")

# Add messages
history.add_user_message("What is RAG?")
history.add_assistant_message("RAG is...")

# Get formatted
text = history.format_as_text(max_messages=10)
llm_messages = history.get_messages_for_llm()

# Check if needs summarization
if history.needs_summarization():
    # Summarize...
    pass
```

---

## 💎 Value Objects Cheat Sheet

### SearchQuery
```python
# Create query
query = SearchQuery(
    text="What is Clean Architecture?",
    top_k=5,
    search_type="hybrid"
)

# Check type
if query.is_product_query():
    collection = "products"
else:
    collection = "documents"
```

### RetrievalConfig
```python
# Use presets
config = RetrievalConfig.for_high_precision()
config = RetrievalConfig.for_high_recall()
config = RetrievalConfig.for_semantic_search()

# Custom config
config = RetrievalConfig(
    top_k=10,
    score_threshold=0.7,
    rerank=True,
    hybrid_alpha=0.5
)

# Add filters
config_with_filters = config.with_filters({"category": "technical"})
```

### LLMConfig
```python
# Use presets
config = LLMConfig.for_creative(model_name="gpt-4o")
config = LLMConfig.for_factual(model_name="gpt-4o-mini")
config = LLMConfig.for_chat(model_name="gpt-4o-mini")

# Custom config
config = LLMConfig(
    model_name="gpt-4o-mini",
    temperature=0.7,
    max_tokens=2000,
    streaming=True
)

# Modify config
new_config = config.with_temperature(0.3)
```

### SearchFilter
```python
# Create filters
filter1 = SearchFilter.by_source("docs/rag.md")
filter2 = SearchFilter.by_category("technical")
filter3 = SearchFilter.by_tags(["rag", "architecture"])

# Combine filters
combined = filter1.combine_with(filter2, operator="AND")

# Convert to Milvus expression
expr = combined.to_milvus_expr()
```

### RAGContext
```python
# Create from documents
context = RAGContext.from_documents(
    documents=[doc1, doc2, doc3],
    query="What is RAG?"
)

# Use context
if context.has_documents():
    formatted = context.format_for_llm(max_length=4000)
    avg_score = context.get_average_score()
    sources = context.get_sources()
```

---

## 🔧 Domain Services Cheat Sheet

### ContextBuilderService
```python
# Create service
builder = ContextBuilderService(
    max_context_length=4000,
    include_metadata=True,
    include_scores=True
)

# Build context
context = builder.build_context(
    documents=[doc1, doc2, doc3],
    query="What is RAG?"
)

# Format documents
formatted = builder.format_documents_for_context(
    documents=[doc1, doc2],
    include_scores=True
)

# Calculate stats
stats = builder.calculate_context_stats(context)
```

### PromptBuilderService
```python
# Create service
builder = PromptBuilderService(
    include_context_header=True,
    include_history_header=True
)

# Build RAG prompt
prompt = builder.build_rag_prompt(
    query="What is RAG?",
    context=rag_context,
    chat_history=[msg1, msg2]
)

# Build chat prompt
prompt = builder.build_chat_prompt(
    query="Hello!",
    chat_history=[msg1, msg2]
)

# Build summarization prompt
prompt = builder.build_summarization_prompt(
    messages=[msg1, msg2, msg3],
    max_length=100
)

# Build query rewrite prompt
prompt = builder.build_rewrite_query_prompt(
    query="it",
    chat_history=[msg1, msg2]
)
```

### ConversationManagerService
```python
# Create service
manager = ConversationManagerService(
    max_messages=20,
    summarization_threshold=12
)

# Add message to session
session = manager.add_message_to_session(session, message)

# Create history
history = manager.create_conversation_history(session)

# Check if should summarize
if manager.should_summarize(history):
    messages = manager.prepare_messages_for_summarization(history)
    # Summarize...
    summary = "..."
    history = manager.apply_summary(history, summary)

# Format for LLM
llm_messages = manager.format_for_llm(history)

# Get stats
stats = manager.calculate_conversation_stats(history)
```

### RetrievalOptimizerService
```python
# Create service
optimizer = RetrievalOptimizerService(
    min_score_threshold=0.7,
    enable_deduplication=True
)

# Optimize results
config = RetrievalConfig.for_high_precision()
optimized = optimizer.optimize_results(result, config)

# Filter by score
filtered = optimizer.filter_by_score(documents, threshold=0.7)

# Deduplicate
unique = optimizer.deduplicate_documents(documents)

# Rerank
reranked = optimizer.rerank_by_query_similarity(
    documents=documents,
    query="What is RAG?",
    boost_factor=1.2
)

# Diversify
diversified = optimizer.diversify_results(
    documents=documents,
    max_per_source=3
)

# Calculate quality
quality = optimizer.calculate_retrieval_quality(result)
```

---

## 📡 Domain Events Cheat Sheet

### Retrieval Events
```python
# Document retrieved
event = DocumentRetrievedEvent(
    query="What is RAG?",
    document_ids=["doc1", "doc2"],
    document_count=2,
    retrieval_strategy="hybrid",
    average_score=0.85
)

# Retrieval completed
event = RetrievalCompletedEvent(
    query="What is RAG?",
    result_id="result123",
    document_count=5,
    retrieval_time_ms=150,
    strategy="hybrid",
    reranked=True
)

# Retrieval failed
event = RetrievalFailedEvent(
    query="What is RAG?",
    error_message="Connection timeout",
    error_type="timeout",
    retry_count=3
)
```

### Conversation Events
```python
# Message received
event = MessageReceivedEvent(
    message_id="msg123",
    session_id="session123",
    user_id="user123",
    message_role="user",
    message_content="What is RAG?"
)

# Response generated
event = ResponseGeneratedEvent(
    message_id="msg124",
    session_id="session123",
    user_id="user123",
    response_content="RAG is...",
    generation_time_ms=2000,
    model_name="gpt-4o-mini",
    token_count=150
)

# Conversation started
event = ConversationStartedEvent(
    session_id="session123",
    user_id="user123",
    initial_message="Hello!"
)

# Conversation ended
event = ConversationEndedEvent(
    session_id="session123",
    user_id="user123",
    message_count=10,
    duration_seconds=300
)
```

### RAG Events
```python
# RAG query received
event = RAGQueryReceivedEvent(
    query="What is RAG?",
    session_id="session123",
    user_id="user123",
    query_type="general"
)

# RAG context built
event = RAGContextBuiltEvent(
    query="What is RAG?",
    session_id="session123",
    document_count=5,
    context_length=2000,
    average_relevance=0.85,
    sources=["doc1.md", "doc2.md"]
)

# RAG response generated
event = RAGResponseGeneratedEvent(
    query="What is RAG?",
    session_id="session123",
    user_id="user123",
    response_length=500,
    generation_time_ms=2000,
    model_name="gpt-4o-mini",
    context_used=True,
    document_count=5,
    token_count=150
)
```

---

## 🎯 Common Patterns

### Pattern 1: RAG Query Flow
```python
# 1. Create query
query = SearchQuery(text="What is RAG?", top_k=5)

# 2. Emit event
event = RAGQueryReceivedEvent(query=query.text)

# 3. Get retrieval result (from infrastructure)
result = RetrievalResult(...)

# 4. Optimize result
optimizer = RetrievalOptimizerService()
config = RetrievalConfig.for_high_precision()
optimized = optimizer.optimize_results(result, config)

# 5. Build context
builder = ContextBuilderService()
context = builder.build_context(optimized.documents, query.text)

# 6. Build prompt
prompt_builder = PromptBuilderService()
prompt = prompt_builder.build_rag_prompt(
    query=query.text,
    context=context,
    chat_history=history.messages
)

# 7. Generate response (via LLM)
# ...

# 8. Emit event
event = RAGResponseGeneratedEvent(...)
```

### Pattern 2: Conversation Management
```python
# 1. Create or load session
session = ChatSession(user_id="user123")

# 2. Add user message
user_msg = Message(content="Hello!", role=MessageRole.USER)
session.add_message(user_msg)

# 3. Create history
manager = ConversationManagerService()
history = manager.create_conversation_history(session)

# 4. Check if summarization needed
if manager.should_summarize(history):
    messages = manager.prepare_messages_for_summarization(history)
    # Summarize...
    summary = "..."
    history = manager.apply_summary(history, summary)

# 5. Format for LLM
llm_messages = manager.format_for_llm(history)

# 6. Generate response
# ...

# 7. Add assistant message
assistant_msg = Message(content="Hi there!", role=MessageRole.ASSISTANT)
session.add_message(assistant_msg)
```

### Pattern 3: Document Processing
```python
# 1. Create documents from search results
documents = [
    Document(content=..., source=..., hybrid_score=...)
    for result in search_results
]

# 2. Filter by score
optimizer = RetrievalOptimizerService()
filtered = optimizer.filter_by_score(documents, threshold=0.7)

# 3. Deduplicate
unique = optimizer.deduplicate_documents(filtered)

# 4. Rerank
reranked = optimizer.rerank_by_query_similarity(
    documents=unique,
    query="What is RAG?"
)

# 5. Take top K
top_k = reranked[:5]

# 6. Build context
builder = ContextBuilderService()
context = builder.build_context(top_k, "What is RAG?")
```

---

## 🧪 Testing Examples

### Test Entity
```python
def test_chat_session():
    session = ChatSession(user_id="user123")
    message = Message(content="Hello", role=MessageRole.USER)
    session.add_message(message)

    assert session.message_count() == 1
    assert session.user_id == "user123"
```

### Test Value Object
```python
def test_search_query_validation():
    # Valid query
    query = SearchQuery(text="test", top_k=5)
    assert query.text == "test"

    # Invalid query
    with pytest.raises(ValueError):
        SearchQuery(text="", top_k=5)
```

### Test Domain Service
```python
def test_context_builder():
    builder = ContextBuilderService(max_context_length=1000)
    documents = [
        Document(content="Test 1", hybrid_score=0.9),
        Document(content="Test 2", hybrid_score=0.8),
    ]

    context = builder.build_context(documents, "test query")

    assert context.has_documents()
    assert context.total_documents == 2
    assert context.get_average_score() == 0.85
```

---

## 📚 Best Practices

### ✅ DO
- Use factory methods for common configurations
- Validate inputs in `__post_init__`
- Keep domain logic pure (no side effects)
- Use type hints everywhere
- Write comprehensive docstrings
- Use enums for type-safe values
- Keep entities focused (SRP)

### ❌ DON'T
- Add infrastructure dependencies
- Mix domain logic with I/O operations
- Create anemic models (data without behavior)
- Use mutable value objects
- Skip validation
- Use magic numbers/strings
- Create god classes

---

## 🔗 Quick Links

- [Full Documentation](./README.md)
- [Architecture Diagram](./ARCHITECTURE.md)
- [Implementation Summary](../../DOMAIN_IMPLEMENTATION_SUMMARY.md)
- [Complete Guide](../../DOMAIN_LAYER_COMPLETE.md)

---

**Domain Layer Quick Reference** - Your go-to cheat sheet! 🚀

