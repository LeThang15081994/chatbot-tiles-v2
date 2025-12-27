"""
RAG (Retrieval-Augmented Generation) Use Case with Tool Calling
Uses LangChain tool calling for intelligent search decision
"""
import time
import uuid
import json
from typing import AsyncGenerator, Optional, List, Dict, Any, TYPE_CHECKING, Callable, TypedDict
from dataclasses import dataclass

if TYPE_CHECKING:
    from app.src.domain.services.summarize_service import SummarizeService
from app.src.application.interfaces.llm_repository import ILLMRepository
from app.src.application.use_cases.search_use_case import SearchUseCase
from app.src.application.dto.chat_dto import (
    ChatRequestDTO,
    ChatResponseDTO,
    ChatMessageDTO,
    WebSocketMessageDTO,
    ChatHistoryResponseDTO
)
from app.src.application.dto.search_dto import (
    SearchRequestDTO,
    SearchResponseDTO,
    SearchResultDTO,
    CollectionType
)
from app.src.infrastructure.guardrails import GuardrailsService
from app.src.infrastructure.observability import LangfuseService
from app.src.domain.services import ContextBuilderService, PromptBuilderService
from app.src.domain.services.summarize_service import SummarizeService


@dataclass
class ToolRegistryEntry:
    """Registry entry for a tool"""
    handler: Callable
    type: str  # "search" or "action"
    intent: Optional[str] = None  # Only for search tools: "company_info", "collection_info", "products"


class RAGUseCase:
    """
    Use case for RAG-based chat functionality with Tool Calling

    Responsibilities:
    - Orchestrate chat flow with RAG using LangChain tool calling
    - Handle streaming and non-streaming responses
    - Manage tool execution (search_docs)
    - Coordinate between vector store, LLM, and cache
    - LLM decides when to search (not always search)
    """

    def __init__(
        self,
        search_use_case: SearchUseCase,
        llm_service: ILLMRepository,
        answer_cache: Optional[Any] = None,  # NEW: AnswerCache (replaces cache_service)
        context_cache: Optional[Any] = None,  # NEW: ContextCache for retriever results
        guardrails_service: Optional[GuardrailsService] = None,
        langfuse_service: Optional[LangfuseService] = None,
        context_builder: Optional[ContextBuilderService] = None,
        prompt_builder: Optional[PromptBuilderService] = None,
        summarize_service: Optional["SummarizeService"] = None,
        shopping_cart_service: Optional[Any] = None
    ):
        """
        Initialize RAG use case

        Args:
            search_use_case: Search use case for document retrieval (used by tool)
            llm_service: LLM repository for generation
            answer_cache: Optional answer cache for LLM responses (replaces cache_service)
            context_cache: Optional context cache for retriever results
            guardrails_service: Optional guardrails service for input/output validation
            langfuse_service: Optional Langfuse service for tracing and observability
            context_builder: Optional context builder service for formatting tool results
            prompt_builder: Optional prompt builder service for building messages
            summarize_service: Optional summarization service for long history
            shopping_cart_service: Optional shopping cart service for add_to_cart action
        """
        self.search_use_case = search_use_case
        self.llm_service = llm_service
        self.answer_cache = answer_cache  # NEW: Answer cache
        self.context_cache = context_cache  # NEW: Context cache
        self.guardrails_service = guardrails_service
        self.langfuse_service = langfuse_service
        self.context_builder = context_builder
        self.prompt_builder = prompt_builder
        self.summarize_service = summarize_service
        self.shopping_cart_service = shopping_cart_service

        # Initialize tool registry
        self._initialize_tool_registry()

    def _initialize_tool_registry(self) -> None:
        """
        Initialize tool registry with all available tools

        Registry maps tool_name to:
        - handler: async function to execute the tool
        - type: "search" or "action"
        - intent: Optional intent for search tools ("company_info", "collection_info", "products")
        """
        # Note: Handler methods are bound methods, so we can reference them directly
        self.TOOL_REGISTRY: Dict[str, ToolRegistryEntry] = {
            "search_company_info": ToolRegistryEntry(
                handler=self._execute_company_info_tool,
                type="search",
                intent="company_info"
            ),
            "search_collection_info": ToolRegistryEntry(
                handler=self._execute_collection_info_tool,
                type="search",
                intent="collection_info"
            ),
            "search_products": ToolRegistryEntry(
                handler=self._execute_products_tool,
                type="search",
                intent="products"
            ),
            "add_to_cart": ToolRegistryEntry(
                handler=self._execute_add_to_cart_tool,
                type="action",
                intent=None
            ),
            "search_docs": ToolRegistryEntry(
                handler=self._execute_search_tool,
                type="search",
                intent="company_info"  # Legacy tool maps to company_info intent
            )
        }

    async def process_chat(
        self,
        request: ChatRequestDTO
    ) -> ChatResponseDTO:
        """
        Process chat request (non-streaming)

        Args:
            request: Chat request DTO

        Returns:
            Chat response DTO
        """
        start_time = time.time()
        session_id = request.session_id or str(uuid.uuid4())
        user_id = request.user_id

        # Initialize Langfuse tracing
        if self.langfuse_service:
            try:
                self.langfuse_service.update_trace(
                    session_id=session_id,
                    user_id=user_id
                )
            except Exception:
                pass  # Continue if Langfuse fails

        # Guardrails input validation
        input_safe = True
        altered_user_message = None
        if self.guardrails_service:
            try:
                # Prepare messages for validation
                validation_messages = [
                    {"role": "user", "content": request.question}
                ]

                validation_result = await self.guardrails_service.validate_input(
                    messages=validation_messages
                )

                input_safe = not validation_result.get("blocked", False)
                altered_user_message = validation_result.get("altered_user_message")

                # If input was blocked, return error response
                if not input_safe:
                    return ChatResponseDTO(
                        answer="I'm sorry, I can't respond to that request. Please ask about ceramic tiles, products, or decoration.",
                        session_id=session_id,
                        user_id=user_id,
                        input_safe=False,
                        output_safe=True,
                        processing_time_ms=int((time.time() - start_time) * 1000)
                    )

                # Use altered message if PII was masked
                if altered_user_message:
                    request.question = altered_user_message

            except Exception as e:
                # Log error but continue processing
                print(f"Guardrails input validation error: {e}")

        # Check answer cache (before LLM call)
        # This uses RedisSemanticCache for semantic similarity matching
        if self.answer_cache:
            cached_answer = await self.answer_cache.get(
                query=request.question,
                namespace="pre-cache"  # Pre-cache: TTL = 20 seconds
            )
            if cached_answer:
                return ChatResponseDTO(
                    answer=cached_answer,
                    session_id=session_id,
                    user_id=user_id,
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )

        # Fetch chat history from Langfuse (giống code cũ)
        chat_history = []
        if self.langfuse_service and session_id:
            try:
                chat_history = self.langfuse_service.get_session_history(
                    session_id=session_id,
                    limit=12
                )
            except Exception:
                chat_history = []

        # Summarize history if too long (giống code cũ)
        if self.summarize_service and len(chat_history) > 4:
            try:
                chat_history = await self.summarize_service.summarize_and_truncate_history(
                    chat_history=chat_history,
                    session_id=session_id,
                    user_id=user_id
                )
            except Exception:
                # Fallback: keep recent messages only
                chat_history = chat_history[-4:] if len(chat_history) > 4 else chat_history

        # Phase 1: Initial LLM call with tools (LLM decides if search needed)
        # Use Domain Service to build initial messages
        if self.prompt_builder:
            initial_messages_dict = self.prompt_builder.build_initial_messages(
                user_query=request.question,
                use_tool_calling=True,
                chat_history=chat_history  # Pass chat history
            )
            initial_messages = [
                ChatMessageDTO(role=msg["role"], content=msg["content"])
                for msg in initial_messages_dict
            ]
        else:
            # Prompt builder is required for tool calling
            raise RuntimeError(
                "PromptBuilderService is required but not provided. "
                "Prompts must be loaded from Langfuse for tool calling."
            )

        # Call LLM with tools (tools already bound in container)
        tool_response = await self.llm_service.generate_with_tools(
            messages=initial_messages,
            tools=[],  # Tools already bound via bind_tools()
            temperature=0.7,
            max_tokens=2048
        )

        # Phase 2: Execute tools if LLM called them
        search_results: List[SearchResultDTO] = []
        products_metadata: List[Dict[str, Any]] = []
        used_intent: Optional[str] = None  # Track intent for prompt selection (only for search tools)

        if tool_response.get("has_tool_calls", False):
            tool_calls = tool_response.get("tool_calls", [])

            # Add assistant message with tool calls
            messages = initial_messages + [
                ChatMessageDTO(
                    role="assistant",
                    content=tool_response.get("content", ""),
                    metadata={"tool_calls": tool_calls}
                )
            ]

            # Execute each tool call using registry-based dispatch
            for tool_call in tool_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})

                # Get tool registry entry
                tool_entry = self.TOOL_REGISTRY.get(tool_name)
                if not tool_entry:
                    # Unknown tool, skip
                    continue

                # Execute tool based on type
                if tool_entry.type == "search":
                    # Search tool: execute and collect results
                    search_results, products_metadata = await tool_entry.handler(tool_args)
                    used_intent = tool_entry.intent  # Store intent for prompt selection

                    # Format tool results using Domain Service
                    if self.context_builder:
                        # Convert SearchResultDTO to format expected by context_builder
                        formatted_results = [
                            {
                                "content": result.content,
                                "score": result.score,
                                "metadata": result.metadata.model_dump() if hasattr(result.metadata, 'model_dump') else result.metadata.dict()
                            }
                            for result in search_results
                        ]
                        tool_result_json = self.context_builder.format_tool_results(
                            search_results=formatted_results,
                            max_content_length=500
                        )
                    else:
                        # Fallback if context_builder not available
                        tool_result_json = json.dumps({
                            "total_results": len(search_results),
                            "results": [
                                {
                                    "content": result.content[:500],
                                    "score": result.score,
                                    "metadata": result.metadata.model_dump() if hasattr(result.metadata, 'model_dump') else result.metadata.dict()
                                }
                                for result in search_results
                            ]
                        }, ensure_ascii=False)

                    messages.append(
                        ChatMessageDTO(
                            role="tool",
                            content=tool_result_json,
                            metadata={"tool_call_id": tool_call.get("id", "")}
                        )
                    )
                elif tool_entry.type == "action":
                    # Action tool: execute and append result, skip RAG generation
                    action_result = await tool_entry.handler(tool_args, request.session_id)
                    tool_result_json = json.dumps(action_result, ensure_ascii=False)
                    messages.append(
                        ChatMessageDTO(
                            role="tool",
                            content=tool_result_json,
                            metadata={"tool_call_id": tool_call.get("id", "")}
                        )
                    )
                    # Action tools don't contribute to search_results or intent
                    continue

            # Phase 3: Final LLM generation with tool results
            # Check if we have action tools that need special formatting
            has_action_tool = any(
                self.TOOL_REGISTRY.get(tc.get("name", ""), ToolRegistryEntry(None, "", None)).type == "action"
                for tc in tool_calls
            )

            if self.prompt_builder and search_results and used_intent:
                # Build RAG prompt with history and context (for search tools)
                # Prompt selection is based on INTENT, not tool_name
                from app.src.domain.value_objects.context import RAGContext
                from app.src.domain.entities.document import Document
                from app.src.domain.entities.message import Message, MessageRole

                # Convert SearchResultDTO to Domain Document entities
                domain_documents = []
                for result in search_results:
                    doc = Document(
                        content=result.content,
                        source=result.metadata.get("source", "") if hasattr(result.metadata, 'get') else (result.metadata.model_dump().get("source", "") if hasattr(result.metadata, 'model_dump') else ""),
                        relevance_score=result.score,
                        metadata=result.metadata.model_dump() if hasattr(result.metadata, 'model_dump') else result.metadata.dict()
                    )
                    domain_documents.append(doc)

                # Build RAG context
                rag_context = RAGContext(documents=domain_documents)

                # Convert chat_history to Message format for prompt_builder
                # Note: chat_history đã được summarize ở Phase 1 (nếu > 4 messages)
                history_messages = []
                for msg in chat_history:
                    role = MessageRole.USER if msg.get("role") == "user" else MessageRole.ASSISTANT
                    history_messages.append(Message(
                        role=role,
                        content=msg.get("content", ""),
                        timestamp=None
                    ))

                # Build RAG prompt with history
                # Prompt selection is based on INTENT (company_info, collection_info, products)
                rag_prompt = self.prompt_builder.build_rag_prompt(
                    query=request.question,
                    context=rag_context,
                    chat_history=history_messages if history_messages else None,
                    intent=used_intent  # Pass intent to select correct prompt
                )

                # Create final messages with RAG prompt (giống code cũ: prompt là string hoàn chỉnh)
                final_messages = [
                    ChatMessageDTO(role="system", content=rag_prompt)
                ]
            elif self.prompt_builder and has_action_tool:
                # For action tools (like add_to_cart), use action_response prompt
                from app.src.domain.entities.message import Message, MessageRole

                # Convert chat_history to Message format for prompt_builder
                history_messages = []
                for msg in chat_history:
                    role = MessageRole.USER if msg.get("role") == "user" else MessageRole.ASSISTANT
                    history_messages.append(Message(
                        role=role,
                        content=msg.get("content", ""),
                        timestamp=None
                    ))

                # Build action response prompt
                action_prompt = self.prompt_builder.build_action_response_prompt(
                    query=request.question,
                    chat_history=history_messages if history_messages else None
                )

                # Create final messages with action response prompt
                # messages already contains tool result, we just need to add system prompt
                final_messages = [
                    ChatMessageDTO(role="system", content=action_prompt)
                ] + messages
            else:
                # Fallback: use messages as is (history already in initial_messages)
                final_messages = messages

            final_response = await self.llm_service.generate_response(
                messages=final_messages,
                temperature=0.7,
                max_tokens=2048
            )
            answer = final_response
        else:
            # No tool calls, use direct response (LLM didn't need search)
            answer = tool_response.get("content", "")

        # Guardrails output validation
        output_safe = True
        if self.guardrails_service and answer:
            try:
                # Validate output
                output_messages = [
                    {"role": "assistant", "content": answer}
                ]
                validation_result = await self.guardrails_service.validate_input(
                    messages=output_messages
                )
                output_safe = not validation_result.get("blocked", False)

                # If output was blocked, return safe response
                if not output_safe:
                    answer = "I apologize, but I cannot provide that response. Please ask about ceramic tiles, products, or decoration."
                    output_safe = True  # Safe response

            except Exception as e:
                # Log error but continue
                print(f"Guardrails output validation error: {e}")

        # Cache the answer
        # If tool calls were made, cache in post-cache (15 minutes)
        # Otherwise, cache in pre-cache (20 seconds)
        if self.answer_cache and answer:
            if tool_response.get("has_tool_calls", False) and messages:
                # Post-cache: after tool execution (TTL = 15 minutes)
                # Build context string from messages for cache key
                context_str = "\n".join([
                    f"{msg.role}: {msg.content}"
                    for msg in messages
                    if msg.content
                ])
                await self.answer_cache.set(
                    query=context_str,
                    answer=answer,
                    namespace="post-cache"  # Post-cache: TTL = 15 minutes
                )
            else:
                # Pre-cache: no tool calls (TTL = 20 seconds)
                await self.answer_cache.set(
                    query=request.question,
                    answer=answer,
                    namespace="pre-cache"  # Pre-cache: TTL = 20 seconds
                )

        processing_time = int((time.time() - start_time) * 1000)

        # Flush Langfuse traces
        if self.langfuse_service:
            try:
                self.langfuse_service.flush()
            except Exception:
                pass

        return ChatResponseDTO(
            answer=answer,
            session_id=session_id,
            user_id=user_id,
            sources=[
                {
                    "content": result.content,
                    "metadata": result.metadata.model_dump() if hasattr(result.metadata, 'model_dump') else result.metadata.model_dump()
                }
                for result in search_results
            ],
            products=products_metadata if products_metadata else None,
            input_safe=input_safe,
            output_safe=output_safe,
            processing_time_ms=processing_time,
            metadata={
                "altered_user_message": altered_user_message is not None,
                "langfuse_traced": self.langfuse_service is not None,
                "tool_calls_used": tool_response.get("has_tool_calls", False)
            }
        )

    async def _execute_company_info_tool(
        self,
        tool_args: Dict[str, Any]
    ) -> tuple[List[SearchResultDTO], List[Dict[str, Any]]]:
        """
        Execute search_company_info tool

        Args:
            tool_args: Tool arguments from LLM (query, top_k)

        Returns:
            Tuple of (search_results, products_metadata)
        """
        query = tool_args.get("query", "")
        top_k = tool_args.get("top_k", 5)

        search_request = SearchRequestDTO(
            query=query,
            top_k=top_k,
            collection_name=CollectionType.COMPANY_DOCUMENT,
            metadata_filter=None
        )

        search_response = await self.search_use_case.search_documents(search_request)
        search_results = search_response.results

        # Company info doesn't have products metadata
        products_metadata = []

        return search_results, products_metadata

    async def _execute_collection_info_tool(
        self,
        tool_args: Dict[str, Any]
    ) -> tuple[List[SearchResultDTO], List[Dict[str, Any]]]:
        """
        Execute search_collection_info tool

        Args:
            tool_args: Tool arguments from LLM (query, top_k)

        Returns:
            Tuple of (search_results, products_metadata)
        """
        query = tool_args.get("query", "")
        top_k = tool_args.get("top_k", 5)

        search_request = SearchRequestDTO(
            query=query,
            top_k=top_k,
            collection_name=CollectionType.COLLECTION_INFO,  # Use collection_info collection
            metadata_filter=None
        )

        search_response = await self.search_use_case.search_documents(search_request)
        search_results = search_response.results

        # Extract collection info metadata
        products_metadata = []
        for result in search_results:
            metadata_dict = result.metadata.model_dump() if hasattr(result.metadata, 'model_dump') else result.metadata.dict()
            collection_name = metadata_dict.get('collection_name') or metadata_dict.get('collectionName')
            if collection_name:
                products_metadata.append({
                    "collectionName": collection_name,
                    "brandName": metadata_dict.get('brand_name') or metadata_dict.get('brandName'),
                })

        return search_results, products_metadata

    async def _execute_products_tool(
        self,
        tool_args: Dict[str, Any]
    ) -> tuple[List[SearchResultDTO], List[Dict[str, Any]]]:
        """
        Execute search_products tool

        Args:
            tool_args: Tool arguments from LLM (query, top_k)

        Returns:
            Tuple of (search_results, products_metadata)
        """
        query = tool_args.get("query", "")
        top_k = tool_args.get("top_k", 5)

        search_request = SearchRequestDTO(
            query=query,
            top_k=top_k,
            collection_name=CollectionType.PRODUCTS,
            metadata_filter=None
        )

        search_response = await self.search_use_case.search_documents(search_request)
        search_results = search_response.results

        # Filter results to only include specific products (where productCode exists)
        filtered_results = []
        products_metadata = []

        for result in search_results:
            metadata_dict = result.metadata.model_dump() if hasattr(result.metadata, 'model_dump') else result.metadata.dict()
            product_code = metadata_dict.get('product_code') or metadata_dict.get('productCode')

            # Only include results that have productCode (specific products, not collection info)
            if product_code:
                filtered_results.append(result)
                products_metadata.append({
                    "productCode": product_code,
                    "brandName": metadata_dict.get('brand_name') or metadata_dict.get('brandName'),
                    "collectionName": metadata_dict.get('collection_name') or metadata_dict.get('collectionName'),
                    "link": metadata_dict.get('link')
                })

        return filtered_results, products_metadata

    async def _execute_add_to_cart_tool(
        self,
        tool_args: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute add_to_cart tool

        Args:
            tool_args: Tool arguments from LLM (product_code, quantity, session_id)
            session_id: Session ID from request (will override tool_args if provided)

        Returns:
            Dictionary with cart operation result
        """
        product_code = tool_args.get("product_code", "")
        quantity = tool_args.get("quantity", 1)
        tool_session_id = tool_args.get("session_id")

        # Use session_id from request if available, otherwise use from tool_args
        final_session_id = session_id or tool_session_id

        if not self.shopping_cart_service:
            return {
                "success": False,
                "error": "Shopping cart service is not available",
                "product_code": product_code
            }

        # Step 1: Search for product by product_code to get productId and price
        # Use product_code as query and filter by productCode in metadata
        search_request = SearchRequestDTO(
            query=product_code,
            top_k=1,
            collection_name=CollectionType.PRODUCTS,
            metadata_filter={"productCode": product_code}  # Try to filter by exact productCode
        )

        try:
            search_response = await self.search_use_case.search_documents(search_request)
            search_results = search_response.results

            # If no results with filter, try without filter (broader search)
            if not search_results:
                search_request = SearchRequestDTO(
                    query=product_code,
                    top_k=5,
                    collection_name=CollectionType.PRODUCTS,
                    metadata_filter=None
                )
                search_response = await self.search_use_case.search_documents(search_request)
                search_results = search_response.results

                # Filter results to find exact productCode match
                filtered_results = []
                for result in search_results:
                    metadata_dict = result.metadata.model_dump() if hasattr(result.metadata, 'model_dump') else result.metadata.dict()
                    result_product_code = metadata_dict.get('product_code') or metadata_dict.get('productCode')
                    if result_product_code and result_product_code.lower() == product_code.lower():
                        filtered_results.append(result)

                if filtered_results:
                    search_results = filtered_results[:1]  # Take first match

            if not search_results:
                return {
                    "success": False,
                    "error": f"Product with code '{product_code}' not found",
                    "product_code": product_code
                }

            # Get product details from first result
            result = search_results[0]
            metadata_dict = result.metadata.model_dump() if hasattr(result.metadata, 'model_dump') else result.metadata.dict()

            # Extract productId and price from metadata
            # Try different possible field names
            product_id = (
                metadata_dict.get('productId') or
                metadata_dict.get('product_id') or
                metadata_dict.get('id')
            )
            price = metadata_dict.get('price') or metadata_dict.get('Price')

            # If productId is not in metadata, try to parse product_code as integer
            if not product_id:
                try:
                    product_id = int(product_code)
                except ValueError:
                    return {
                        "success": False,
                        "error": f"Could not find productId for product code '{product_code}'. Product may not exist in the system.",
                        "product_code": product_code
                    }

            # Convert product_id to int
            try:
                product_id = int(product_id)
            except (ValueError, TypeError):
                return {
                    "success": False,
                    "error": f"Invalid productId format for product code '{product_code}'",
                    "product_code": product_code
                }

            # If price is not in metadata, default to 0 (API might handle this)
            if price is None:
                price = 0.0
            else:
                try:
                    price = float(price)
                except (ValueError, TypeError):
                    price = 0.0

            # Step 2: Call shopping cart API
            cart_result = await self.shopping_cart_service.add_to_cart(
                product_id=product_id,
                quantity=quantity,
                price=price,
                session_id=final_session_id
            )

            return cart_result

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to add product to cart: {str(e)}",
                "product_code": product_code
            }

    async def _execute_search_tool(
        self,
        tool_args: Dict[str, Any]
    ) -> tuple[List[SearchResultDTO], List[Dict[str, Any]]]:
        """
        Execute search_docs tool

        Args:
            tool_args: Tool arguments from LLM

        Returns:
            Tuple of (search_results, products_metadata)
        """
        query = tool_args.get("query", "")
        top_k = tool_args.get("top_k", 5)
        collection_name_str = tool_args.get("collection_name")

        collection_type = CollectionType.AUTO
        if collection_name_str:
            try:
                collection_type = CollectionType(collection_name_str.lower())
            except ValueError:
                collection_type = CollectionType.AUTO

        search_request = SearchRequestDTO(
            query=query,
            top_k=top_k,
            collection_name=collection_type,
            metadata_filter=None
        )

        search_response = await self.search_use_case.search_documents(search_request)
        search_results = search_response.results

        # Extract products metadata
        products_metadata = []
        for result in search_results:
            metadata_dict = result.metadata.model_dump() if hasattr(result.metadata, 'model_dump') else result.metadata.dict()
            product_code = metadata_dict.get('product_code') or metadata_dict.get('productCode')
            if product_code:
                products_metadata.append({
                    "productCode": product_code,
                    "brandName": metadata_dict.get('brand_name') or metadata_dict.get('brandName'),
                    "collectionName": metadata_dict.get('collection_name') or metadata_dict.get('collectionName'),
                    "link": metadata_dict.get('link')
                })

        return search_results, products_metadata

    async def stream_chat(
        self,
        request: ChatRequestDTO
    ) -> AsyncGenerator[WebSocketMessageDTO, None]:
        """
        Process chat request with streaming

        Args:
            request: Chat request DTO

        Yields:
            WebSocket message DTOs
        """
        # Send metadata first
        session_id = request.session_id or str(uuid.uuid4())
        user_id = request.user_id or f"user_{str(uuid.uuid4())[:8]}"

        # Initialize Langfuse tracing
        if self.langfuse_service:
            try:
                self.langfuse_service.update_trace(
                    session_id=session_id,
                    user_id=user_id
                )
            except Exception:
                pass  # Continue if Langfuse fails

        yield WebSocketMessageDTO(
            type="metadata",
            data={
                "session_id": session_id,
                "user_id": user_id
            }
        )

        # Guardrails input validation
        input_safe = True
        altered_user_message = None
        if self.guardrails_service:
            try:
                validation_messages = [
                    {"role": "user", "content": request.question}
                ]

                validation_result = await self.guardrails_service.validate_input(
                    messages=validation_messages
                )

                input_safe = not validation_result.get("blocked", False)
                altered_user_message = validation_result.get("altered_user_message")

                # If input was blocked, send error and return
                if not input_safe:
                    yield WebSocketMessageDTO(
                        type="error",
                        data="I'm sorry, I can't respond to that request. Please ask about ceramic tiles, products, or decoration.",
                        metadata={"input_blocked": True}
                    )
                    yield WebSocketMessageDTO(type="done", data="[END]")
                    return

                # Use altered message if PII was masked
                if altered_user_message:
                    request.question = altered_user_message

            except Exception as e:
                print(f"Guardrails input validation error: {e}")

        # Check answer cache (before LLM call)
        if self.answer_cache:
            cached_response = await self.answer_cache.get(
                query=request.question,
                namespace="pre-cache"  # Pre-cache: TTL = 20 seconds
            )
            if cached_response:
                yield WebSocketMessageDTO(
                    type="content",
                    data=cached_response,
                    metadata={"cached": True}
                )
                yield WebSocketMessageDTO(type="done", data="[END]")
                return

        # Fetch chat history from Langfuse (giống code cũ)
        chat_history = []
        if self.langfuse_service and session_id:
            try:
                chat_history = self.langfuse_service.get_session_history(
                    session_id=session_id,
                    limit=12
                )
            except Exception:
                chat_history = []

        # Summarize history if too long (giống code cũ)
        if self.summarize_service and len(chat_history) > 4:
            try:
                chat_history = await self.summarize_service.summarize_and_truncate_history(
                    chat_history=chat_history,
                    session_id=session_id,
                    user_id=user_id
                )
            except Exception:
                # Fallback: keep recent messages only
                chat_history = chat_history[-4:] if len(chat_history) > 4 else chat_history

        # Phase 1: Initial LLM call with tools (detect if search needed)
        # Use Domain Service to build initial messages
        if self.prompt_builder:
            initial_messages_dict = self.prompt_builder.build_initial_messages(
                user_query=request.question,
                use_tool_calling=True,
                chat_history=chat_history  # Pass chat history
            )
            initial_messages = [
                ChatMessageDTO(role=msg["role"], content=msg["content"])
                for msg in initial_messages_dict
            ]
        else:
            # Prompt builder is required for tool calling
            raise RuntimeError(
                "PromptBuilderService is required but not provided. "
                "Prompts must be loaded from Langfuse for tool calling."
            )

        # Stream with tools
        full_response = ""
        search_results: List[SearchResultDTO] = []
        products_metadata: List[Dict[str, Any]] = []
        tool_calls_detected = False
        used_intent: Optional[str] = None  # Track intent for prompt selection (only for search tools)

        async for chunk in self.llm_service.stream_with_tools(
            messages=initial_messages,
            tools=[],  # Tools already bound
            temperature=0.7,
            max_tokens=2048
        ):
            chunk_type = chunk.get("type", "")

            if chunk_type == "content":
                # Stream content chunk
                content = chunk.get("content", "")
                full_response += content
                yield WebSocketMessageDTO(
                    type="content",
                    data=content
                )

            elif chunk_type == "tool_calls":
                # Tool calls detected
                tool_calls_detected = True
                tool_calls = chunk.get("tool_calls", [])

                # Execute tools
                messages = initial_messages + [
                    ChatMessageDTO(
                        role="assistant",
                        content=full_response,
                        metadata={"tool_calls": tool_calls}
                    )
                ]

                # Execute each tool call using registry-based dispatch
                for tool_call in tool_calls:
                    tool_name = tool_call.get("name")
                    tool_args = tool_call.get("args", {})

                    # Get tool registry entry
                    tool_entry = self.TOOL_REGISTRY.get(tool_name)
                    if not tool_entry:
                        # Unknown tool, skip
                        continue

                    # Execute tool based on type
                    if tool_entry.type == "search":
                        # Search tool: execute and collect results
                        search_results, products_metadata = await tool_entry.handler(tool_args)
                        used_intent = tool_entry.intent  # Store intent for prompt selection

                        # Format tool results using Domain Service
                        if self.context_builder:
                            formatted_results = [
                                {
                                    "content": result.content,
                                    "score": result.score,
                                    "metadata": result.metadata.model_dump() if hasattr(result.metadata, 'model_dump') else result.metadata.dict()
                                }
                                for result in search_results
                            ]
                            tool_result_json = self.context_builder.format_tool_results(
                                search_results=formatted_results,
                                max_content_length=500
                            )
                        else:
                            # Fallback if context_builder not available
                            tool_result_json = json.dumps({
                                "total_results": len(search_results),
                                "results": [
                                    {
                                        "content": result.content[:500],
                                        "score": result.score,
                                        "metadata": result.metadata.model_dump() if hasattr(result.metadata, 'model_dump') else result.metadata.dict()
                                    }
                                    for result in search_results
                                ]
                            }, ensure_ascii=False)

                        messages.append(
                            ChatMessageDTO(
                                role="tool",
                                content=tool_result_json,
                                metadata={"tool_call_id": tool_call.get("id", "")}
                            )
                        )
                    elif tool_entry.type == "action":
                        # Action tool: execute and append result, skip RAG generation
                        action_result = await tool_entry.handler(tool_args, session_id)
                        tool_result_json = json.dumps(action_result, ensure_ascii=False)
                        messages.append(
                            ChatMessageDTO(
                                role="tool",
                                content=tool_result_json,
                                metadata={"tool_call_id": tool_call.get("id", "")}
                            )
                        )
                        # Action tools don't contribute to search_results or intent
                        continue

                # Check post-cache (after tool execution, based on messages with tool results)
                # Similar to code cũ: @semantic_cache_llms.cache(namespace="post-cache")
                if self.answer_cache and messages:
                    # Build context string from messages for cache key
                    context_str = "\n".join([
                        f"{msg.role}: {msg.content}"
                        for msg in messages
                        if msg.content
                    ])

                    cached_response = await self.answer_cache.get(
                        query=context_str,
                        namespace="post-cache"  # Post-cache: TTL = 15 minutes
                    )
                    if cached_response:
                        yield WebSocketMessageDTO(
                            type="content",
                            data=cached_response
                        )
                        yield WebSocketMessageDTO(type="done", data="[END]")
                        return

                # Phase 3: Stream final response with tool results
                # Check if we have action tools that need special formatting
                has_action_tool = any(
                    self.TOOL_REGISTRY.get(tc.get("name", ""), ToolRegistryEntry(None, "", None)).type == "action"
                    for tc in tool_calls
                )

                if self.prompt_builder and search_results and used_intent:
                    # Convert search results to RAG context
                    from app.src.domain.value_objects.context import RAGContext
                    from app.src.domain.entities.document import Document
                    from app.src.domain.entities.message import Message, MessageRole

                    # Convert SearchResultDTO to Domain Document entities
                    domain_documents = []
                    for result in search_results:
                        doc = Document(
                            content=result.content,
                            source=result.metadata.get("source", "") if hasattr(result.metadata, 'get') else (result.metadata.model_dump().get("source", "") if hasattr(result.metadata, 'model_dump') else ""),
                            relevance_score=result.score,
                            metadata=result.metadata.model_dump() if hasattr(result.metadata, 'model_dump') else result.metadata.dict()
                        )
                        domain_documents.append(doc)

                    # Build RAG context
                    rag_context = RAGContext(documents=domain_documents)

                    # Convert chat_history to Message format for prompt_builder
                    # Note: chat_history đã được summarize ở Phase 1 (nếu > 4 messages)
                    history_messages = []
                    for msg in chat_history:
                        role = MessageRole.USER if msg.get("role") == "user" else MessageRole.ASSISTANT
                        history_messages.append(Message(
                            role=role,
                            content=msg.get("content", ""),
                            timestamp=None
                        ))

                    # Build RAG prompt with history
                    # Prompt selection is based on INTENT (company_info, collection_info, products)
                    rag_prompt = self.prompt_builder.build_rag_prompt(
                        query=request.question,
                        context=rag_context,
                        chat_history=history_messages if history_messages else None,
                        intent=used_intent  # Pass intent to select correct prompt
                    )

                    # Create final messages with RAG prompt (giống code cũ: prompt là string hoàn chỉnh)
                    final_messages = [
                        ChatMessageDTO(role="system", content=rag_prompt)
                    ]
                elif self.prompt_builder and has_action_tool:
                    # For action tools (like add_to_cart), use action_response prompt
                    from app.src.domain.entities.message import Message, MessageRole

                    # Convert chat_history to Message format for prompt_builder
                    history_messages = []
                    for msg in chat_history:
                        role = MessageRole.USER if msg.get("role") == "user" else MessageRole.ASSISTANT
                        history_messages.append(Message(
                            role=role,
                            content=msg.get("content", ""),
                            timestamp=None
                        ))

                    # Build action response prompt
                    action_prompt = self.prompt_builder.build_action_response_prompt(
                        query=request.question,
                        chat_history=history_messages if history_messages else None
                    )

                    # Create final messages with action response prompt
                    # messages already contains tool result, we just need to add system prompt
                    final_messages = [
                        ChatMessageDTO(role="system", content=action_prompt)
                    ] + messages
                else:
                    # Fallback: use messages as is (history already in initial_messages)
                    final_messages = messages

                full_response = ""
                async for content_chunk in self.llm_service.stream_response(
                    messages=final_messages,
                    temperature=0.7,
                    max_tokens=2048
                ):
                    full_response += content_chunk
                    yield WebSocketMessageDTO(
                        type="content",
                        data=content_chunk
                    )

            elif chunk_type == "final":
                # Final chunk - no tool calls, use direct response
                if not tool_calls_detected:
                    final_content = chunk.get("content", "")
                    if final_content:
                        full_response = final_content
                        # Stream the response
                        for char in final_content:
                            yield WebSocketMessageDTO(
                                type="content",
                                data=char
                            )

        # Guardrails output validation
        output_safe = True
        if self.guardrails_service and full_response:
            try:
                output_messages = [{"role": "assistant", "content": full_response}]
                validation_result = await self.guardrails_service.validate_input(
                    messages=output_messages
                )
                output_safe = not validation_result.get("blocked", False)

                if not output_safe:
                    error_message = "I apologize, but I cannot provide that response. Please ask about ceramic tiles, products, or decoration."
                    full_response = error_message
                    yield WebSocketMessageDTO(
                        type="error",
                        data=error_message,
                        metadata={"output_blocked": True}
                    )
            except Exception as e:
                print(f"Guardrails output validation error: {e}")

        # Send products if any
        if products_metadata:
            yield WebSocketMessageDTO(
                type="products",
                data=products_metadata
            )

        # Cache response
        # If tool calls were made, cache in post-cache (15 minutes)
        # Otherwise, cache in pre-cache (20 seconds)
        if self.cache_service and full_response:
            # Check if we have messages with tool results (from stream)
            # tool_calls_detected is set during streaming
            if tool_calls_detected and 'messages' in locals() and messages:
                # Post-cache: after tool execution (TTL = 15 minutes)
                # Build context string from messages for cache key
                context_str = "\n".join([
                    f"{msg.role}: {msg.content}"
                    for msg in messages
                    if msg.content
                ])
                await self.answer_cache.set(
                    query=context_str,
                    answer=full_response,
                    namespace="post-cache"  # Post-cache: TTL = 15 minutes
                )
            else:
                # Pre-cache: no tool calls (TTL = 20 seconds)
                await self.answer_cache.set(
                    query=request.question,
                    answer=full_response,
                    namespace="pre-cache"  # Pre-cache: TTL = 20 seconds
                )

        # Flush Langfuse traces
        if self.langfuse_service:
            try:
                self.langfuse_service.flush()
            except Exception:
                pass

        # Send done signal
        yield WebSocketMessageDTO(
            type="done",
            data="[END]",
            metadata={
                "input_safe": input_safe,
                "output_safe": output_safe,
                "altered_user_message": altered_user_message is not None,
                "tool_calls_used": tool_calls_detected
            }
        )

    async def get_chat_history(
        self,
        session_id: str,
        limit: int = 12
    ) -> ChatHistoryResponseDTO:
        """
        Get chat history for a session from Langfuse (giống code cũ)

        Args:
            session_id: Session ID
            limit: Maximum number of messages to return

        Returns:
            Chat history response DTO
        """
        # Fetch from Langfuse (giống code cũ)
        chat_history = []
        if self.langfuse_service:
            try:
                chat_history = self.langfuse_service.get_session_history(
                    session_id=session_id,
                    limit=limit
                )
            except Exception:
                chat_history = []

        # Convert to ChatMessageDTO format
        messages = []
        for msg in chat_history:
            messages.append(
                ChatMessageDTO(
                    role=msg.get("role", "user"),
                    content=msg.get("content", ""),
                    timestamp=None
                )
            )

        return ChatHistoryResponseDTO(
            session_id=session_id,
            messages=messages,
            total_count=len(messages)
        )


