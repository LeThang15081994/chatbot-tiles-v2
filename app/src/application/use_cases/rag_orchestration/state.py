"""
LangGraph State Definition

Local to orchestration module, not exported as domain entity.
This state exists only for LangGraph's state machine execution.
"""
from typing import TypedDict, List, Dict, Any, Optional, Literal

from app.src.application.dto.chat_dto import ChatMessageDTO
from app.src.application.dto.search_dto import SearchResultDTO


class GraphState(TypedDict, total=False):
    """
    LangGraph state for RAG orchestration

    This is a LOCAL construct, not a domain entity.
    It exists only for LangGraph's state machine execution.

    Note: total=False allows partial state updates (nodes can return only changed fields)
    """
    # Input
    query: str  # User's question
    initial_messages: List[ChatMessageDTO]  # Initial messages from PromptBuilderService
    chat_history: List[Dict[str, str]]  # Chat history (already summarized if needed)

    # Decision
    need_tool: bool  # Whether tool execution is needed
    intent: Optional[Literal["company_info", "collection_info", "products", "add_to_cart"]]  # Search intent or action intent

    # Action tool payload and result
    action_payload: Optional[Dict[str, Any]]  # Action payload (e.g., {"product_id": str, "quantity": int}) - only when intent == "add_to_cart"
    action_result: Optional[Dict[str, Any]]  # Action execution result (success/failure/cart snapshot)

    # Tool execution results
    search_results: List[SearchResultDTO]  # Search results from tools
    products_metadata: List[Dict[str, Any]]  # Product metadata extracted from search

    # Final output
    final_answer: Optional[str]  # Final generated answer
    messages: List[ChatMessageDTO]  # Message history for LLM

    # Metadata
    has_action_tool: bool  # Whether action tools (like add_to_cart) were used
    session_id: Optional[str]  # Session ID for action tools

    # Guardrails validation
    input_validated: bool  # Whether input passed guardrails validation
    input_blocked: bool  # Whether input was blocked by guardrails

    # Streaming support
    streaming_chunks: List[str]  # Streaming chunks from generate_answer_node (for streaming mode)
    streaming_complete: bool  # Whether streaming is complete

