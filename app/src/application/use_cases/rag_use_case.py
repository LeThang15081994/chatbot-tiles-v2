"""RAG Use Case with Tool Calling - LangChain tool calling for intelligent search"""
import time
import uuid
import json
import logging
import asyncio
from typing import AsyncGenerator, Optional, List, Dict, Any, TYPE_CHECKING, Callable, TypedDict
from dataclasses import dataclass

if TYPE_CHECKING:
    from app.src.domain.services.summarize_service import SummarizeService
    from langchain_core.tools import StructuredTool

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
from app.src.application.interfaces.services.guardrails_interface import IGuardrailsService
from app.src.application.interfaces.services.tracing_interface import ITracingService
from app.src.domain.services.context_builder import ContextBuilderService
from app.src.domain.services.prompt_builder import PromptBuilderService
from app.src.domain.services.summarize_service import SummarizeService
from app.src.domain.services.answer_cache_facade import AnswerCacheFacade
from app.src.application.use_cases.rag_orchestration import build_rag_graph, build_rag_streaming_graph

logger = logging.getLogger(__name__)


class RAGUseCase:
    """RAG-based chat with Tool Calling - orchestrates chat flow, tool execution, and caching"""

    def __init__(
        self,
        search_use_case: SearchUseCase,
        llm_service: Any,
        answer_cache_facade: Optional[AnswerCacheFacade] = None,
        context_cache: Optional[Any] = None,
        llm_raise: Optional[IGuardrailsService] = None,
        tracing_service: Optional[ITracingService] = None,
        context_builder: Optional[ContextBuilderService] = None,
        prompt_builder: Optional[PromptBuilderService] = None,
        summarize_service: Optional["SummarizeService"] = None,
        shopping_cart_service: Optional[Any] = None,
        structured_tools: Optional[Dict[str, "StructuredTool"]] = None
    ):
        """Initialize RAG use case"""
        self.search_use_case = search_use_case
        self.llm_service = llm_service
        self.answer_cache_facade = answer_cache_facade
        self.context_cache = context_cache
        self.llm_raise = llm_raise
        self.tracing_service = tracing_service
        self.context_builder = context_builder
        self.prompt_builder = prompt_builder
        self.summarize_service = summarize_service
        self.shopping_cart_service = shopping_cart_service
        self.structured_tools = structured_tools or {}  # LangChain StructuredTool dict

    async def process_chat(self, request: ChatRequestDTO) -> ChatResponseDTO:
        """Process chat request (non-streaming) with 4-layer caching and tool calling"""
        start_time = time.time()
        session_id = request.session_id or str(uuid.uuid4())
        user_id = request.user_id

        # Initialize Langfuse tracing
        if self.tracing_service:
            try:
                self.tracing_service.update_trace(
                    session_id=session_id,
                    user_id=user_id
                )
            except Exception:
                pass  # Continue if Langfuse fails

        # Step 1: Check 4-layer cache (includes guardrails input validation)
        query_vector = None
        input_safe = True

        if self.answer_cache_facade:
            cache_result = await self.answer_cache_facade.check_cache(request.question)
            if cache_result.is_blocked:
                return ChatResponseDTO(
                    answer="I'm sorry, I can't respond to that request. Please ask about ceramic tiles, products, or decoration.",
                    session_id=session_id,
                    user_id=user_id,
                    input_safe=False,
                    output_safe=True,
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )
            if cache_result.is_hit:
                return ChatResponseDTO(
                    answer=cache_result.answer,
                    session_id=session_id,
                    user_id=user_id,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    metadata={"cache_hit": cache_result.cache_hit_layer}
                )
            query_vector = cache_result.query_vector


        # Fetch chat history from Langfuse (giống code cũ)
        chat_history = []
        if self.tracing_service and session_id:
            try:
                chat_history = self.tracing_service.get_session_history(
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

        # Phase 1: Build initial messages (for LangGraph state)
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
            # Prompt builder is required
            raise RuntimeError(
                "PromptBuilderService is required but not provided. "
                "Prompts must be loaded from Langfuse for tool calling."
            )

        # Build LangGraph with injected dependencies
        langfuse_handler = None
        if self.tracing_service:
            try:
                langfuse_handler = self.tracing_service.get_callback_handler()
            except Exception:
                pass  # Continue if Langfuse handler not available

        graph = build_rag_graph(
            llm_service=self.llm_service,
            prompt_builder=self.prompt_builder,
            structured_tools=self.structured_tools,  # LangChain StructuredTool dict
            context_builder=self.context_builder,
            chat_history=chat_history,
            session_id=session_id,  # Pass session_id for action tools
            langfuse_handler=langfuse_handler,  # Langfuse callback handler for tracing
            guardrails_service=self.llm_raise  # Guardrails service for input/output validation
        )

        # Initialize state for LangGraph
        initial_state = {
            "query": request.question,
            "initial_messages": initial_messages,
            "chat_history": chat_history,
            "need_tool": False,
            "intent": None,
            "action_payload": None,  # For action tools
            "action_result": None,  # For action tool results
            "search_results": [],
            "products_metadata": [],
            "final_answer": None,
            "messages": [],
            "has_action_tool": False,
            "session_id": session_id,  # Session ID for action tools
            "input_validated": False,  # Guardrails input validation flag
            "input_blocked": False  # Guardrails input blocked flag
        }

        # Execute LangGraph
        final_state = await graph.ainvoke(initial_state)

        # Extract results from LangGraph state
        answer = final_state.get("final_answer", "")
        search_results = final_state.get("search_results", [])
        products_metadata = final_state.get("products_metadata", [])
        used_intent = final_state.get("intent")

        # Guardrails validation status (already handled in graph)
        input_validated = final_state.get("input_validated", True)
        input_blocked = final_state.get("input_blocked", False)
        # Output validation is handled in guardrails_output_node, so output is safe if it reaches here
        output_safe = True

        # Write answer to 4-layer cache
        if self.answer_cache_facade and answer:
            await self.answer_cache_facade.write_to_cache(
                raw_text=request.question,
                answer=answer,
                query_vector=query_vector
            )


        processing_time = int((time.time() - start_time) * 1000)

        # Flush Langfuse traces
        if self.tracing_service:
            try:
                self.tracing_service.flush()
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
                "traced": self.tracing_service is not None,
                "tool_calls_used": bool(search_results) or bool(used_intent)  # Tools used if we have search results or intent
            }
        )

    # NOTE: Tool handler methods removed - all tools now use LangChain StructuredTool
    # Tools are executed via StructuredTool instances in structured_tools dict
    # See: app/src/presentation/llm/search_tool.py for tool implementations

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
        if self.tracing_service:
            try:
                self.tracing_service.update_trace(
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

        # Check answer cache (before LLM call) - using answer_cache_facade
        if self.answer_cache_facade:
            cache_result = await self.answer_cache_facade.check_cache(request.question)
            if cache_result.is_hit:
                yield WebSocketMessageDTO(
                    type="content",
                    data=cache_result.answer,
                    metadata={"cached": True}
                )
                yield WebSocketMessageDTO(type="done", data="[END]")
                return

        # Fetch chat history from Langfuse (giống code cũ)
        chat_history = []
        if self.tracing_service and session_id:
            try:
                chat_history = self.tracing_service.get_session_history(
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

        # Phase 1: Build initial messages (for LangGraph state)
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
            # Prompt builder is required
            raise RuntimeError(
                "PromptBuilderService is required but not provided. "
                "Prompts must be loaded from Langfuse for tool calling."
            )

        # Build LangGraph with streaming support
        langfuse_handler = None
        if self.tracing_service:
            try:
                langfuse_handler = self.tracing_service.get_callback_handler()
            except Exception:
                pass  # Continue if Langfuse handler not available

        # Create transport mechanism for real-time streaming
        streaming_queue = asyncio.Queue()
        graph = build_rag_streaming_graph(
            llm_service=self.llm_service,
            prompt_builder=self.prompt_builder,
            structured_tools=self.structured_tools,  # LangChain StructuredTool dict
            context_builder=self.context_builder,
            chat_history=chat_history,
            session_id=session_id,  # Pass session_id for action tools
            langfuse_handler=langfuse_handler,
            guardrails_service=self.llm_raise,
            streaming_queue=streaming_queue
        )

        # Initialize state for LangGraph
        initial_state = {
            "query": request.question,
            "initial_messages": initial_messages,
            "chat_history": chat_history,
            "need_tool": False,
            "intent": None,
            "action_payload": None,  # For action tools
            "action_result": None,  # For action tool results
            "search_results": [],
            "products_metadata": [],
            "final_answer": None,
            "messages": [],
            "has_action_tool": False,
            "session_id": session_id,  # Session ID for action tools
            "input_validated": False,
            "input_blocked": False,
            "streaming_chunks": [],
            "streaming_complete": False
        }

        # Initialize tracking variables
        full_response = ""
        search_results: List[SearchResultDTO] = []
        products_metadata: List[Dict[str, Any]] = []
        tool_calls_detected = False
        used_intent: Optional[str] = None
        input_safe = True
        output_safe = True
        altered_user_message = None

        # Run graph in background and consume chunks real-time
        graph_task = asyncio.create_task(
            self._run_graph_with_state_tracking(graph, initial_state, session_id)
        )
        final_state = None
        graph_error = None
        try:
            while True:
                try:
                    chunk = await asyncio.wait_for(streaming_queue.get(), timeout=300.0)
                    if chunk is None:
                        break
                    if chunk and isinstance(chunk, str):
                        full_response += chunk
                        yield WebSocketMessageDTO(type="content", data=chunk)
                    streaming_queue.task_done()
                except asyncio.TimeoutError:
                    logger.warning("Timeout waiting for streaming chunks", extra={"session_id": session_id})
                    break
                except Exception as e:
                    logger.error("Error consuming from streaming queue", exc_info=True, extra={"error_type": type(e).__name__, "session_id": session_id})
                    graph_error = e
                    break

        except Exception as e:
            logger.error(
                "Error during real-time streaming",
                exc_info=True,
                extra={
                    "error_type": type(e).__name__,
                    "session_id": session_id
                }
            )
            graph_error = e

        finally:
            try:
                final_state = await graph_task
            except Exception as e:
                logger.error("Error in graph execution", exc_info=True, extra={"error_type": type(e).__name__, "session_id": session_id})
                if not graph_error:
                    graph_error = e

        if graph_error:
            yield WebSocketMessageDTO(type="error", data="An error occurred while processing your request. Please try again.", metadata={"error": str(graph_error)})
            yield WebSocketMessageDTO(type="done", data="[END]")
            return

        # Check if input was blocked
        if final_state and final_state.get("input_blocked", False):
            yield WebSocketMessageDTO(
                type="error",
                data="I'm sorry, I can't respond to that request. Please ask about ceramic tiles, products, or decoration.",
                metadata={"input_blocked": True}
            )
            yield WebSocketMessageDTO(type="done", data="[END]")
            return

        # Extract final values from state
        if final_state:
            final_answer = final_state.get("final_answer")
            if final_answer and isinstance(final_answer, str) and not full_response:
                full_response = final_answer
            if final_state.get("search_results"):
                search_results = final_state.get("search_results")
            if final_state.get("products_metadata"):
                products_metadata = final_state.get("products_metadata")
            input_safe = not final_state.get("input_blocked", False)
            output_safe = True
        else:
            logger.warning("Final state is None after graph execution", extra={"session_id": session_id})
            if not full_response:
                full_response = "I apologize, but I encountered an error while generating a response. Please try again."
                yield WebSocketMessageDTO(type="error", data=full_response, metadata={"error": "empty_response"})

        # Send products if any
        if products_metadata and isinstance(products_metadata, list) and len(products_metadata) > 0:
            yield WebSocketMessageDTO(
                type="products",
                data=products_metadata
            )

        # Cache response
        if self.answer_cache_facade and full_response and isinstance(full_response, str) and full_response.strip():
            try:
                await self.answer_cache_facade.write_to_cache(
                    raw_text=request.question,
                    answer=full_response
                )
            except Exception as e:
                # Log error but don't fail the request
                logger.error(
                    "Failed to write to cache",
                    exc_info=True,
                    extra={
                        "error_type": type(e).__name__,
                        "session_id": session_id
                    }
                )

        # Flush Langfuse traces
        if self.tracing_service:
            try:
                self.tracing_service.flush()
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

    async def _run_graph_with_state_tracking(
        self,
        graph: Any,
        initial_state: Dict[str, Any],
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Run graph in background and track state updates"""
        final_state = None
        try:
            async for state_update in graph.astream(initial_state):
                if final_state is None:
                    final_state = dict(initial_state)
                for key, value in state_update.items():
                    final_state[key] = value
                if state_update.get("input_blocked", False):
                    break
            return final_state
        except Exception as e:
            logger.error("Error in graph execution", exc_info=True, extra={"error_type": type(e).__name__, "session_id": session_id})
            return None

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
        if self.tracing_service:
            try:
                chat_history = self.tracing_service.get_session_history(
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


