# Vai trò của LangChain trong Code Cũ

## 📋 KẾT LUẬN

### ✅ Code cũ dùng LangChain để:
1. **Tạo và quản lý Tools** (StructuredTool)
2. **Bind tools vào LLM** (llm.bind_tools())
3. **Tool Calling** - LLM tự động detect và gọi tools
4. **Vector Store Integration** (langchain_milvus)
5. **LLM Wrapper** (ChatOpenAI)

### ✅ Tool search CÓ được LangChain quản lý

---

## 1. 🔧 LANGCHAIN TRONG CODE CŨ - Vai trò chính

### 1.1. Tool Management (Quản lý Tools)

**LangChain cung cấp:**
- `StructuredTool` - Class để tạo tools từ functions
- `bind_tools()` - Method để bind tools vào LLM
- Tool calling mechanism - LLM tự động detect và gọi tools

**Code cũ sử dụng:**
```python
# chat-backend/src/services/application/rag.py

from langchain.tools import StructuredTool
from pydantic import BaseModel

# 1. Define SearchArgs schema
class SearchArgs(BaseModel):
    query: str
    top_k: int = 5
    collection_name: Optional[str] = None

# 2. Define search function
async def search_docs(query: str, top_k: int = 5, collection_name: Optional[str] = None):
    """Search documents in knowledge base"""
    # ... search logic ...
    return results

# 3. Tạo StructuredTool từ function
search_tool = StructuredTool.from_function(
    func=search_docs,                    # Function thực thi
    name="search_docs",                  # Tool name
    description="Search documents in the knowledge base about ceramic tiles",
    args_schema=SearchArgs               # Pydantic schema cho arguments
)
```

**Vai trò của LangChain:**
- ✅ **Tạo tool definition** - Convert function → tool schema
- ✅ **Validate arguments** - Sử dụng Pydantic schema
- ✅ **Generate tool description** - Cho LLM biết tool làm gì
- ✅ **Tool metadata** - Name, description, parameters

---

### 1.2. Tool Binding (Gắn Tools vào LLM)

**LangChain cung cấp:**
- `llm.bind_tools(tools)` - Bind tools vào LLM instance
- LLM sẽ biết có những tools nào available

**Code cũ sử dụng:**
```python
# chat-backend/src/services/application/rag.py

from langchain_openai import ChatOpenAI

# 1. Initialize LLM
llm = ChatOpenAI(
    model="groq",
    base_url="http://litellm-router-llmops:4000",
    api_key="gach-llmops"
)

# 2. Bind tools vào LLM
llm_with_tools = llm.bind_tools([search_tool])
# → LLM giờ biết có tool "search_docs" available
```

**Vai trò của LangChain:**
- ✅ **Tool registration** - Đăng ký tools với LLM
- ✅ **Tool schema generation** - Tạo JSON schema cho LLM
- ✅ **LLM integration** - LLM có thể detect và gọi tools

---

### 1.3. Tool Calling (LLM gọi Tools)

**LangChain cung cấp:**
- Automatic tool detection - LLM tự động detect khi nào cần gọi tool
- Tool call format - Standard format cho tool calls
- Tool response handling - Xử lý response từ tools

**Code cũ sử dụng:**
```python
# chat-backend/src/services/application/rag.py

# 1. Initial LLM call (với tools bound)
messages = [
    {"role": "user", "content": "What is wooden tile?"}
]

response = await llm_with_tools.ainvoke(messages)

# 2. LangChain tự động detect tool calls
if response.tool_calls:
    # response.tool_calls = [
    #     {
    #         "name": "search_docs",
    #         "args": {"query": "wooden tile", "top_k": 5},
    #         "id": "call_123"
    #     }
    # ]

    # 3. Execute tools
    for tool_call in response.tool_calls:
        if tool_call["name"] == "search_docs":
            # Execute search
            results = await search_docs(**tool_call["args"])

            # 4. Add tool message (LangChain format)
            messages.append({
                "role": "tool",
                "content": results,
                "tool_call_id": tool_call["id"]
            })

    # 5. Final LLM call với tool results
    final_response = await llm_with_tools.ainvoke(messages)
```

**Vai trò của LangChain:**
- ✅ **Tool detection** - LLM tự động detect khi nào cần tool
- ✅ **Tool call format** - Standard format (name, args, id)
- ✅ **Tool message format** - Standard format cho tool responses
- ✅ **Multi-turn conversation** - Hỗ trợ tool → LLM → tool

---

### 1.4. Vector Store Integration

**LangChain cung cấp:**
- `langchain_milvus.Milvus` - Wrapper cho Milvus vector store
- `BM25BuiltInFunction` - BM25 search support
- Document format - Standard document format

**Code cũ sử dụng:**
```python
# chat-backend/src/services/application/rag.py

from langchain_milvus import Milvus, BM25BuiltInFunction

# Initialize Milvus với LangChain wrapper
vector_store = Milvus(
    collection_name="company_document",
    embedding_function=embedding_function,
    connection_args={"host": "milvus", "port": "19530"}
)

# Hybrid search với LangChain
results = vector_store.similarity_search_with_score(
    query=query,
    k=top_k,
    search_type="hybrid"  # Vector + BM25
)
```

**Vai trò của LangChain:**
- ✅ **Vector store abstraction** - Unified interface
- ✅ **Hybrid search** - Vector + BM25
- ✅ **Document format** - Standard LangChain Document

---

### 1.5. LLM Wrapper

**LangChain cung cấp:**
- `ChatOpenAI` - Wrapper cho OpenAI-compatible APIs
- Streaming support - `astream()`, `astream_events()`
- Message format - Standard chat message format

**Code cũ sử dụng:**
```python
# chat-backend/src/services/application/rag.py

from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="groq",
    base_url="http://litellm-router-llmops:4000",
    api_key="gach-llmops",
    temperature=0.7,
    streaming=True
)

# Streaming với LangChain
async for chunk in llm.astream(messages):
    yield chunk.content
```

**Vai trò của LangChain:**
- ✅ **LLM abstraction** - Unified interface cho nhiều providers
- ✅ **Streaming** - Built-in streaming support
- ✅ **Message format** - Standard format

---

## 2. 🔍 TOOL SEARCH CÓ ĐƯỢC LANGCHAIN QUẢN LÝ KHÔNG?

### ✅ CÓ - Tool search được LangChain quản lý hoàn toàn

**Quy trình:**

#### Bước 1: Tạo Tool (LangChain quản lý)
```python
search_tool = StructuredTool.from_function(
    func=search_docs,
    name="search_docs",
    description="...",
    args_schema=SearchArgs
)
# → LangChain tạo tool schema, validate function signature
```

#### Bước 2: Bind Tool (LangChain quản lý)
```python
llm_with_tools = llm.bind_tools([search_tool])
# → LangChain đăng ký tool với LLM
# → LLM biết có tool "search_docs" available
```

#### Bước 3: Tool Detection (LangChain quản lý)
```python
response = await llm_with_tools.ainvoke(messages)
# → LangChain format tool calls trong response
# → response.tool_calls = [{"name": "search_docs", "args": {...}, "id": "..."}]
```

#### Bước 4: Tool Execution (Developer quản lý)
```python
# Developer tự execute tool
results = await search_docs(**tool_call["args"])
```

#### Bước 5: Tool Response (LangChain quản lý)
```python
messages.append({
    "role": "tool",
    "content": results,
    "tool_call_id": tool_call["id"]
})
# → LangChain format cho tool messages
```

#### Bước 6: Final Generation (LangChain quản lý)
```python
final_response = await llm_with_tools.ainvoke(messages)
# → LangChain xử lý tool messages và generate final response
```

---

## 3. 📊 SO SÁNH: CODE CŨ vs CODE MỚI

### 3.1. Code Cũ (Có LangChain Tool Management)

| Component | LangChain Role | Status |
|-----------|----------------|--------|
| **Tool Creation** | `StructuredTool.from_function()` | ✅ LangChain quản lý |
| **Tool Binding** | `llm.bind_tools()` | ✅ LangChain quản lý |
| **Tool Detection** | Automatic trong `ainvoke()` | ✅ LangChain quản lý |
| **Tool Execution** | Developer execute | ⚠️ Developer quản lý |
| **Tool Response** | LangChain format | ✅ LangChain quản lý |
| **Final Generation** | LangChain xử lý | ✅ LangChain quản lý |

**Kết luận:**
- ✅ **Tool search được LangChain quản lý 90%**
- ⚠️ **Chỉ tool execution là developer tự làm**

---

### 3.2. Code Mới (Không có LangChain Tool Management)

| Component | Current Status | LangChain Role |
|-----------|----------------|----------------|
| **Tool Creation** | ❌ Không có | - |
| **Tool Binding** | ❌ Không có | - |
| **Tool Detection** | ❌ Không có | - |
| **Search Execution** | ✅ Direct call | ⚠️ Không qua LangChain |
| **Tool Response** | ❌ Không có | - |
| **Final Generation** | ✅ Direct call | ⚠️ Không qua LangChain |

**Kết luận:**
- ❌ **Code mới KHÔNG có tool management**
- ❌ **Search là direct call, không qua LangChain tool system**

---

## 4. 🎯 TÓM TẮT

### Code Cũ dùng LangChain để:

1. ✅ **Tạo Tools** - `StructuredTool.from_function()`
2. ✅ **Bind Tools** - `llm.bind_tools([search_tool])`
3. ✅ **Tool Calling** - LLM tự động detect và gọi tools
4. ✅ **Vector Store** - `langchain_milvus.Milvus`
5. ✅ **LLM Wrapper** - `ChatOpenAI`

### Tool search có được LangChain quản lý không?

**✅ CÓ - Tool search được LangChain quản lý:**

- ✅ **Tool definition** - LangChain tạo từ function
- ✅ **Tool registration** - LangChain bind vào LLM
- ✅ **Tool detection** - LangChain detect trong LLM response
- ✅ **Tool format** - LangChain format tool calls/messages
- ⚠️ **Tool execution** - Developer tự execute (nhưng theo LangChain format)

**Flow:**
```
Developer Function
  ↓
LangChain StructuredTool (quản lý)
  ↓
LangChain bind_tools() (quản lý)
  ↓
LLM với tools (LangChain quản lý)
  ↓
LLM detect tool calls (LangChain quản lý)
  ↓
Developer execute tool (tự làm)
  ↓
LangChain tool message format (quản lý)
  ↓
LLM final generation (LangChain quản lý)
```

---

## 5. 📝 CODE MỚI CẦN LÀM GÌ ĐỂ GIỐNG CODE CŨ?

### 5.1. Sử dụng LangChain Tool Management

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

    # ✅ LangChain quản lý tool
    return StructuredTool.from_function(
        func=search_docs,
        name="search_docs",
        description="Search documents in the knowledge base about ceramic tiles",
        args_schema=SearchArgs
    )
```

### 5.2. Bind Tools vào LLM

```python
# app/src/bootstrap/container.py

# Tạo search tool
search_tool = create_search_tool(search_use_case)

# Bind tools vào LLM (LangChain quản lý)
llm_client.bind_tools([search_tool])
```

### 5.3. Sử dụng Tool Calling trong RAGUseCase

```python
# app/src/application/use_cases/rag_use_case.py

# Initial LLM call với tools (LangChain quản lý)
response = await self.llm_service.generate_with_tools(
    messages=messages,
    tools=[search_tool]
)

# LangChain tự động detect tool calls
if response.tool_calls:
    # Execute tools
    for tool_call in response.tool_calls:
        if tool_call["name"] == "search_docs":
            results = await execute_search_tool(tool_call)
            # LangChain format cho tool message
            messages.append({
                "role": "tool",
                "content": results,
                "tool_call_id": tool_call["id"]
            })

    # Final generation (LangChain quản lý)
    final_response = await self.llm_service.generate_response(messages)
```

---

## 6. ✅ KẾT LUẬN

### Code Cũ:
- ✅ **Dùng LangChain để quản lý tools** (StructuredTool, bind_tools)
- ✅ **Tool search được LangChain quản lý** (90% workflow)
- ✅ **LLM tự động detect và gọi tools** (qua LangChain)

### Code Mới:
- ❌ **KHÔNG dùng LangChain tool management**
- ❌ **Search là direct call, không qua LangChain**
- ❌ **Không có tool calling mechanism**

### Để giống code cũ:
- ✅ Cần implement LangChain tool management
- ✅ Tạo StructuredTool từ search function
- ✅ Bind tools vào LLM
- ✅ Sử dụng tool calling flow

