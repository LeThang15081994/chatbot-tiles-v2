"""
Decision Nodes

LLM-based decision making for routing and intent detection.
"""
import json
import logging
from typing import Dict, Any, Optional, TYPE_CHECKING

from app.src.application.dto.chat_dto import ChatMessageDTO
from app.src.application.use_cases.rag_orchestration.state import GraphState
from app.src.application.use_cases.error_handle_use_cases import (
    LLMDecisionError,
    JSONParseError
)

if TYPE_CHECKING:
    from app.src.application.interfaces.services.llm_service_interface import ILLMService
    from app.src.domain.services.prompt_builder import PromptBuilderService
    from langfuse.langchain import CallbackHandler

logger = logging.getLogger(__name__)


async def llm_decide_node(
    state: GraphState,
    llm_service: "ILLMService",  # ILLMService interface (injected)
    prompt_builder: "PromptBuilderService",  # PromptBuilderService (injected, has prompts from Langfuse)
    langfuse_handler: Optional["CallbackHandler"] = None  # Langfuse CallbackHandler (injected)
) -> Dict[str, Any]:
    """
    Decision node: LLM decides whether to call tools and which intent

    RESPONSIBILITY:
    - Uses prompt from Langfuse (via prompt_builder) for routing decision
    - Calls LLM with routing prompt (NOT tool calling, NOT StructuredTool)
    - Returns JSON decision only
    - Does NOT call tools, embeddings, or generate user-facing answers

    ARCHITECTURE:
    - This is a LangGraph orchestration node, NOT a LangChain tool
    - Uses prompt from Langfuse Dashboard (via prompt_builder.prompt_userinput)
    - LLM call is traced via Langfuse handler

    EMBEDDING NOTE:
    - This node MUST NEVER trigger embeddings
    - It only calls LLM with a simple routing prompt
    - No vector search, no embedding generation

    Args:
        state: Current graph state
        llm_service: LLM service (injected dependency)
        prompt_builder: Prompt builder service with Langfuse prompts (injected)
        langfuse_handler: Langfuse callback handler for tracing (injected)

    Returns:
        Updated state with need_tool and intent decisions
    """
    try:
        # Use prompt from Langfuse (via prompt_builder)
        # This ensures prompt management is centralized in Langfuse Dashboard
        query_preview = state["query"][:100] if len(state["query"]) > 100 else state["query"]
        logger.debug(f"Building routing decision for query: '{query_preview}'")

        initial_messages_dict = prompt_builder.build_initial_messages(
            user_query=state["query"],
            use_tool_calling=True,
            chat_history=None  # No history for routing decision
        )

        # Convert to ChatMessageDTO
        routing_messages = [
            ChatMessageDTO(role=msg["role"], content=msg["content"])
            for msg in initial_messages_dict
        ]

        # Append routing instructions to Langfuse prompt
        routing_instruction = """

Based on the above instructions, analyze the user's question and decide:
1. Does the user need information from documents? (need_tool: true/false)
2. If yes, what type of information? (intent: "company_info", "collection_info", "products", or "add_to_cart")
3. If intent is "add_to_cart", extract product_id and quantity from the user's message

Respond with JSON only:
{
    "need_tool": true/false,
    "intent": "company_info" | "collection_info" | "products" | "add_to_cart" | null,
    "action_payload": {
        "product_id": string,
        "quantity": number
    } | null
}

Rules:
- action_payload MUST be present ONLY when intent == "add_to_cart"
- action_payload MUST be null for all other intents
- If intent is "add_to_cart", extract product_id (can be product code or ID) and quantity (default to 1 if not specified)"""

        # Append to system message
        if routing_messages and routing_messages[0].role == "system":
            routing_messages[0].content += routing_instruction

        # Call LLM with Langfuse tracing
        config = {}
        if langfuse_handler:
            config["callbacks"] = [langfuse_handler]

        # Use generate_response (not generate_with_tools) - this is just routing
        response_text = await llm_service.generate_response(
            messages=routing_messages,
            temperature=0.3,  # Lower temperature for more consistent routing
            max_tokens=100,
            **config  # Pass callbacks for Langfuse tracing
        )

        logger.debug(f"LLM routing response received: {response_text[:200]}")

    except Exception as e:
        # LLM call failed
        logger.error(
            "LLM decision call failed",
            exc_info=True,
            extra={
                "error_type": type(e).__name__,
                "query": state.get("query", "")[:100]
            }
        )
        # Fallback: assume no tool needed
        need_tool = False
        intent = None
        action_payload = None

        return {
            "need_tool": need_tool,
            "intent": intent,
            "messages": state.get("messages", []) + state.get("initial_messages", [])
        }

    # Parse JSON response
    try:
        # response_text should be defined from the try block above
        if 'response_text' not in locals():
            raise ValueError("LLM response not available")
        # Extract JSON from response (handle markdown code blocks)
        response_text = response_text.strip()
        original_response = response_text

        if response_text.startswith("```"):
            # Remove markdown code blocks
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])
        elif response_text.startswith("```json"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])

        decision = json.loads(response_text)
        need_tool = decision.get("need_tool", False)
        intent = decision.get("intent")
        action_payload = decision.get("action_payload")

        logger.debug(
            "LLM decision parsed",
            extra={
                "need_tool": need_tool,
                "intent": intent,
                "has_action_payload": action_payload is not None
            }
        )

        # Validate intent
        valid_intents = ["company_info", "collection_info", "products", "add_to_cart", None]
        if intent not in valid_intents:
            logger.warning(
                f"Invalid intent received: {intent}, falling back to None",
                extra={"intent": intent, "valid_intents": valid_intents}
            )
            intent = None
            action_payload = None

        # Validate action_payload: must be present only when intent == "add_to_cart"
        if intent != "add_to_cart":
            action_payload = None
        elif intent == "add_to_cart" and not action_payload:
            # If intent is add_to_cart but no payload, try to extract from query
            # This is a fallback - ideally LLM should provide it
            logger.warning(
                "add_to_cart intent without payload, using default",
                extra={"query": state.get("query", "")[:100]}
            )
            action_payload = {"product_id": "", "quantity": 1}

    except json.JSONDecodeError as e:
        # JSON parsing failed
        logger.error(
            "Failed to parse LLM decision JSON",
            exc_info=True,
            extra={
                "error_type": "JSONParseError",
                "raw_response": original_response[:200] if 'original_response' in locals() else response_text[:200],
                "query": state.get("query", "")[:100]
            }
        )
        # Fallback: assume no tool needed if parsing fails
        need_tool = False
        intent = None
        action_payload = None

    except KeyError as e:
        # Missing required key in decision
        logger.warning(
            f"Missing key in LLM decision: {e}",
            extra={
                "missing_key": str(e),
                "query": state.get("query", "")[:100]
            }
        )
        need_tool = False
        intent = None
        action_payload = None

    except Exception as e:
        # Unexpected error during parsing
        logger.error(
            "Unexpected error parsing LLM decision",
            exc_info=True,
            extra={
                "error_type": type(e).__name__,
                "query": state.get("query", "")[:100]
            }
        )
        need_tool = False
        intent = None
        action_payload = None

    # Return partial state update (LangGraph merges with existing state)
    state_update = {
        "need_tool": need_tool,
        "intent": intent,
        "messages": state.get("messages", []) + state["initial_messages"]
    }

    # Add action_payload only when intent is add_to_cart
    if intent == "add_to_cart" and action_payload:
        state_update["action_payload"] = action_payload

    return state_update

