"""
Tool Nodes

Nodes for executing action tools (e.g., add_to_cart).
"""
import json
import logging
from typing import Dict, Any, Optional, TYPE_CHECKING

from app.src.application.use_cases.rag_orchestration.state import GraphState
from app.src.application.use_cases.error_handle_use_cases import (
    ToolExecutionError,
    StateValidationError
)

if TYPE_CHECKING:
    from langchain_core.tools import StructuredTool
    from langfuse.langchain import CallbackHandler

logger = logging.getLogger(__name__)

# LangChain StructuredTool import
try:
    from langchain_core.tools import StructuredTool
except ImportError:
    StructuredTool = None


async def add_to_cart_node(
    state: GraphState,
    structured_tools: Dict[str, "StructuredTool"],  # LangChain StructuredTool dict (injected)
    session_id: Optional[str] = None,  # Session ID (injected)
    langfuse_handler: Optional["CallbackHandler"] = None  # Langfuse CallbackHandler (injected)
) -> Dict[str, Any]:
    """
    Execute add_to_cart action using LangChain StructuredTool

    RESPONSIBILITY:
    - Receives action_payload from state
    - Calls LangChain StructuredTool (add_to_cart)
    - Returns action_result (success / failure / cart snapshot)
    - NO prompt logic
    - NO LLM calls
    - NO business logic (all logic in StructuredTool implementation)

    ARCHITECTURE:
    - Uses LangChain StructuredTool for tool execution
    - Tool execution is traced via Langfuse handler

    EMBEDDING NOTE:
    - This node MAY indirectly trigger embeddings (via tool execution → SearchUseCase → VectorStore)
    - The StructuredTool searches for products before adding to cart

    Args:
        state: Current graph state
        structured_tools: Dict of LangChain StructuredTool instances (injected)
        session_id: Session ID for cart operations (injected)
        langfuse_handler: Langfuse callback handler for tracing (injected)

    Returns:
        Updated state with action_result
    """
    # Get action_payload from state
    action_payload = state.get("action_payload")
    if not action_payload:
        logger.warning(
            "add_to_cart called without action_payload",
            extra={"state_keys": list(state.keys())}
        )
        return {
            "action_result": {
                "success": False,
                "error": "No action payload provided",
                "action": "add_to_cart"
            }
        }

    # Get StructuredTool from dict
    tool = structured_tools.get("add_to_cart")
    if not tool:
        logger.error("add_to_cart tool not available in structured_tools")
        return {
            "action_result": {
                "success": False,
                "error": "add_to_cart tool not available",
                "action": "add_to_cart"
            }
        }

    # Execute via StructuredTool
    config = {}
    if langfuse_handler:
        config["callbacks"] = [langfuse_handler]

    product_id = action_payload.get("product_id", "")
    quantity = action_payload.get("quantity", 1)
    logger.info(
        "Executing add_to_cart action",
        extra={
            "product_id": product_id,
            "quantity": quantity,
            "session_id": session_id or state.get("session_id")
        }
    )

    try:
        # Prepare tool args (StructuredTool expects: product_code, quantity, session_id)
        tool_result_json = await tool.ainvoke(
            {
                "product_code": product_id,  # product_id can be product_code
                "quantity": quantity,
                "session_id": session_id or state.get("session_id")
            },
            config=config
        )

        # Parse JSON result
        action_result = json.loads(tool_result_json)

        # Ensure action_result has action field
        if isinstance(action_result, dict):
            action_result["action"] = "add_to_cart"

        success = action_result.get("success", False)
        logger.info(
            f"add_to_cart action {'succeeded' if success else 'failed'}",
            extra={
                "success": success,
                "product_id": product_id,
                "error": action_result.get("error") if not success else None
            }
        )

    except json.JSONDecodeError as e:
        logger.error(
            "Failed to parse add_to_cart tool result JSON",
            exc_info=True,
            extra={
                "error_type": "JSONDecodeError",
                "tool_name": "add_to_cart",
                "product_id": product_id
            }
        )
        action_result = {
            "success": False,
            "error": f"Failed to parse tool response: {str(e)}",
            "action": "add_to_cart"
        }
    except Exception as e:
        # Tool execution failed
        logger.error(
            "add_to_cart tool execution failed",
            exc_info=True,
            extra={
                "error_type": type(e).__name__,
                "tool_name": "add_to_cart",
                "product_id": product_id
            }
        )
        action_result = {
            "success": False,
            "error": f"Tool execution failed: {str(e)}",
            "action": "add_to_cart"
        }

    # Return partial state update
    return {
        "action_result": action_result,
        "has_action_tool": True
    }

