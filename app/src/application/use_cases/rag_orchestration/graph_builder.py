"""
LangGraph Builder

Builds and compiles LangGraph workflow.
"""
import asyncio
from typing import Dict, Any, List, Optional

from app.src.application.use_cases.rag_orchestration.state import GraphState
from app.src.application.use_cases.rag_orchestration.nodes import (
    guardrails_input_node,
    guardrails_output_node,
    llm_decide_node,
    search_company_node,
    search_collection_node,
    search_products_node,
    generate_answer_node,
    generate_answer_streaming_node,
    add_to_cart_node
)
from app.src.application.use_cases.rag_orchestration.routing import should_use_tool

# LangGraph imports (may not be installed yet, but will be at runtime)
try:
    from langgraph.graph import StateGraph, END
except ImportError:
    # Fallback for development (will fail at runtime if not installed)
    StateGraph = None
    END = None

# LangChain StructuredTool import
try:
    from langchain_core.tools import StructuredTool
except ImportError:
    StructuredTool = None


def build_rag_graph(
    llm_service: Any,
    prompt_builder: Any,
    structured_tools: Dict[str, StructuredTool],
    context_builder: Any,
    chat_history: List[Dict[str, str]],
    session_id: Optional[str] = None,
    langfuse_handler: Optional[Any] = None,
    guardrails_service: Optional[Any] = None
) -> StateGraph:
    """Build LangGraph for RAG orchestration"""
    workflow = StateGraph(GraphState)
    async def guardrails_input_wrapper(state: GraphState) -> Dict[str, Any]:
        return await guardrails_input_node(
            state,
            guardrails_service=guardrails_service,
            langfuse_handler=langfuse_handler
        )

    async def guardrails_output_wrapper(state: GraphState) -> Dict[str, Any]:
        return await guardrails_output_node(
            state,
            guardrails_service=guardrails_service,
            langfuse_handler=langfuse_handler
        )

    async def llm_decide_wrapper(state: GraphState) -> Dict[str, Any]:
        return await llm_decide_node(
            state,
            llm_service=llm_service,
            prompt_builder=prompt_builder,
            langfuse_handler=langfuse_handler
        )

    async def search_company_wrapper(state: GraphState) -> Dict[str, Any]:
        return await search_company_node(
            state,
            structured_tools=structured_tools,
            context_builder=context_builder,
            langfuse_handler=langfuse_handler
        )

    async def search_collection_wrapper(state: GraphState) -> Dict[str, Any]:
        return await search_collection_node(
            state,
            structured_tools=structured_tools,
            context_builder=context_builder,
            langfuse_handler=langfuse_handler
        )

    async def search_products_wrapper(state: GraphState) -> Dict[str, Any]:
        return await search_products_node(
            state,
            structured_tools=structured_tools,
            context_builder=context_builder,
            langfuse_handler=langfuse_handler
        )

    async def generate_answer_wrapper(state: GraphState) -> Dict[str, Any]:
        return await generate_answer_node(
            state,
            llm_service=llm_service,
            prompt_builder=prompt_builder,
            chat_history=chat_history,
            langfuse_handler=langfuse_handler
        )

    async def add_to_cart_wrapper(state: GraphState) -> Dict[str, Any]:
        return await add_to_cart_node(
            state,
            structured_tools=structured_tools,
            session_id=session_id,
            langfuse_handler=langfuse_handler
        )

    workflow.add_node("guardrails_input", guardrails_input_wrapper)
    workflow.add_node("llm_decide", llm_decide_wrapper)
    workflow.add_node("search_company", search_company_wrapper)
    workflow.add_node("search_collection", search_collection_wrapper)
    workflow.add_node("search_products", search_products_wrapper)
    workflow.add_node("add_to_cart", add_to_cart_wrapper)
    workflow.add_node("generate_answer", generate_answer_wrapper)
    workflow.add_node("guardrails_output", guardrails_output_wrapper)

    workflow.set_entry_point("guardrails_input")

    def should_continue_after_input_validation(state: GraphState) -> str:
        """Route after input validation"""
        if state.get("input_blocked", False):
            return "end_blocked"
        return "llm_decide"

    workflow.add_conditional_edges("guardrails_input", should_continue_after_input_validation, {"end_blocked": END, "llm_decide": "llm_decide"})
    workflow.add_conditional_edges("llm_decide", should_use_tool, {"generate_answer": "generate_answer", "search_company": "search_company", "search_collection": "search_collection", "search_products": "search_products", "add_to_cart": "add_to_cart"})
    workflow.add_edge("search_company", "generate_answer")
    workflow.add_edge("search_collection", "generate_answer")
    workflow.add_edge("search_products", "generate_answer")
    workflow.add_edge("add_to_cart", "generate_answer")
    workflow.add_edge("generate_answer", "guardrails_output")
    workflow.add_edge("guardrails_output", END)

    return workflow.compile()


def build_rag_streaming_graph(
    llm_service: Any,
    prompt_builder: Any,
    structured_tools: Dict[str, StructuredTool],
    context_builder: Any,
    chat_history: List[Dict[str, str]],
    session_id: Optional[str] = None,
    langfuse_handler: Optional[Any] = None,
    guardrails_service: Optional[Any] = None,
    streaming_queue: Optional[asyncio.Queue] = None
) -> StateGraph:
    """Build LangGraph for RAG orchestration with real-time streaming support"""
    workflow = StateGraph(GraphState)
    async def guardrails_input_wrapper(state: GraphState) -> Dict[str, Any]:
        return await guardrails_input_node(
            state,
            guardrails_service=guardrails_service,
            langfuse_handler=langfuse_handler
        )

    async def guardrails_output_wrapper(state: GraphState) -> Dict[str, Any]:
        return await guardrails_output_node(
            state,
            guardrails_service=guardrails_service,
            langfuse_handler=langfuse_handler
        )

    async def llm_decide_wrapper(state: GraphState) -> Dict[str, Any]:
        return await llm_decide_node(
            state,
            llm_service=llm_service,
            prompt_builder=prompt_builder,
            langfuse_handler=langfuse_handler
        )

    async def search_company_wrapper(state: GraphState) -> Dict[str, Any]:
        return await search_company_node(
            state,
            structured_tools=structured_tools,
            context_builder=context_builder,
            langfuse_handler=langfuse_handler
        )

    async def search_collection_wrapper(state: GraphState) -> Dict[str, Any]:
        return await search_collection_node(
            state,
            structured_tools=structured_tools,
            context_builder=context_builder,
            langfuse_handler=langfuse_handler
        )

    async def search_products_wrapper(state: GraphState) -> Dict[str, Any]:
        return await search_products_node(
            state,
            structured_tools=structured_tools,
            context_builder=context_builder,
            langfuse_handler=langfuse_handler
        )

    async def generate_answer_streaming_wrapper(state: GraphState) -> Dict[str, Any]:
        return await generate_answer_streaming_node(state, llm_service=llm_service, prompt_builder=prompt_builder, chat_history=chat_history, streaming_queue=streaming_queue, langfuse_handler=langfuse_handler)

    async def add_to_cart_wrapper(state: GraphState) -> Dict[str, Any]:
        return await add_to_cart_node(
            state,
            structured_tools=structured_tools,
            session_id=session_id,
            langfuse_handler=langfuse_handler
        )

    workflow.add_node("guardrails_input", guardrails_input_wrapper)
    workflow.add_node("llm_decide", llm_decide_wrapper)
    workflow.add_node("search_company", search_company_wrapper)
    workflow.add_node("search_collection", search_collection_wrapper)
    workflow.add_node("search_products", search_products_wrapper)
    workflow.add_node("add_to_cart", add_to_cart_wrapper)
    workflow.add_node("generate_answer", generate_answer_streaming_wrapper)
    workflow.add_node("guardrails_output", guardrails_output_wrapper)

    workflow.set_entry_point("guardrails_input")

    def should_continue_after_input_validation(state: GraphState) -> str:
        """Route after input validation"""
        if state.get("input_blocked", False):
            return "end_blocked"
        return "llm_decide"

    workflow.add_conditional_edges("guardrails_input", should_continue_after_input_validation, {"end_blocked": END, "llm_decide": "llm_decide"})
    workflow.add_conditional_edges("llm_decide", should_use_tool, {"generate_answer": "generate_answer", "search_company": "search_company", "search_collection": "search_collection", "search_products": "search_products", "add_to_cart": "add_to_cart"})
    workflow.add_edge("search_company", "generate_answer")
    workflow.add_edge("search_collection", "generate_answer")
    workflow.add_edge("search_products", "generate_answer")
    workflow.add_edge("add_to_cart", "generate_answer")
    workflow.add_edge("generate_answer", "guardrails_output")
    workflow.add_edge("guardrails_output", END)

    return workflow.compile()

