"""
Conditional Routing Logic

Pure functions for LangGraph conditional edges.
"""
from typing import Literal

from app.src.application.use_cases.rag_orchestration.state import GraphState


def should_use_tool(
    state: GraphState
) -> Literal["generate_answer", "search_company", "search_collection", "search_products", "add_to_cart"]:
    """
    Conditional routing after llm_decide_node

    Routes based on:
    - need_tool == false → generate_answer
    - intent == company_info → search_company
    - intent == collection_info → search_collection
    - intent == products → search_products
    - intent == add_to_cart → add_to_cart

    Args:
        state: Current graph state

    Returns:
        Next node name
    """
    need_tool = state.get("need_tool", False)
    intent = state.get("intent")

    if not need_tool:
        return "generate_answer"

    if intent == "company_info":
        return "search_company"
    elif intent == "collection_info":
        return "search_collection"
    elif intent == "products":
        return "search_products"
    elif intent == "add_to_cart":
        return "add_to_cart"
    else:
        # Fallback: generate answer if intent is unclear
        return "generate_answer"

