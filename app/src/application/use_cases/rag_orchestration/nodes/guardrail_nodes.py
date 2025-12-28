"""
Guardrails Nodes

Input and output validation nodes using Guardrails service.
"""
import logging
from typing import Dict, Any, Optional, TYPE_CHECKING

from app.src.application.use_cases.rag_orchestration.state import GraphState
from app.src.application.use_cases.error_handle_use_cases import (
    GuardrailsError,
    GuardrailsServiceError
)

if TYPE_CHECKING:
    from app.src.application.interfaces.services.guardrails_interface import IGuardrailsService
    from langfuse.langchain import CallbackHandler

logger = logging.getLogger(__name__)


async def guardrails_input_node(
    state: GraphState,
    guardrails_service: Optional["IGuardrailsService"],
    langfuse_handler: Optional["CallbackHandler"] = None
) -> Dict[str, Any]:
    """Validate input with guardrails before processing"""
    if not guardrails_service:
        logger.debug("Guardrails service not available, skipping input validation")
        return {"input_validated": True, "input_blocked": False}

    try:
        query_preview = state["query"][:100] if len(state["query"]) > 100 else state["query"]
        logger.debug(f"Validating input with guardrails: query_preview='{query_preview}'")

        validation_result = await guardrails_service.validate_input(
            messages=[{"role": "user", "content": state["query"]}]
        )

        blocked = validation_result.get("blocked", False)
        altered = validation_result.get("altered", False)
        altered_user_message = validation_result.get("altered_user_message")

        if blocked:
            logger.warning(
                "Input blocked by guardrails",
                extra={
                    "query_preview": query_preview,
                    "validation_type": "input",
                    "blocked": True
                }
            )
            return {
                "input_validated": True,
                "input_blocked": True,
                "final_answer": "I'm sorry, I can't respond to that request. Please ask about ceramic tiles, products, or decoration."
            }

        state_update = {"input_validated": True, "input_blocked": False}
        if altered and altered_user_message:
            logger.info(
                "Input altered by guardrails (PII masking)",
                extra={
                    "query_preview": query_preview,
                    "altered": True
                }
            )
            state_update["query"] = altered_user_message

        logger.debug("Input validation passed")
        return state_update
    except GuardrailsServiceError as e:
        logger.error("Guardrails service error during input validation", exc_info=True, extra={"error_type": type(e).__name__, "error_code": e.error_code, "query_preview": state.get("query", "")[:100]})
        return {"input_validated": False, "input_blocked": False}
    except Exception as e:
        logger.error("Unexpected error in guardrails input validation", exc_info=True, extra={"error_type": type(e).__name__, "query_preview": state.get("query", "")[:100]})
        return {"input_validated": False, "input_blocked": False}


async def guardrails_output_node(
    state: GraphState,
    guardrails_service: Optional["IGuardrailsService"],
    langfuse_handler: Optional["CallbackHandler"] = None
) -> Dict[str, Any]:
    """Validate output with guardrails after generation"""
    if not guardrails_service:
        logger.debug("Guardrails service not available, skipping output validation")
        return {}

    final_answer = state.get("final_answer")
    if not final_answer:
        logger.debug("No final answer to validate")
        return {}

    try:
        answer_preview = final_answer[:100] if len(final_answer) > 100 else final_answer
        logger.debug(f"Validating output with guardrails: answer_preview='{answer_preview}'")

        validation_result = await guardrails_service.validate_input(
            messages=[{"role": "assistant", "content": final_answer}]
        )

        blocked = validation_result.get("blocked", False)
        if blocked:
            logger.warning("Output blocked by guardrails", extra={"answer_preview": answer_preview, "validation_type": "output", "blocked": True})
            return {"final_answer": "I apologize, but I cannot provide that response. Please ask about ceramic tiles, products, or decoration."}

        logger.debug("Output validation passed")
        return {}
    except GuardrailsServiceError as e:
        logger.error("Guardrails service error during output validation", exc_info=True, extra={"error_type": type(e).__name__, "error_code": e.error_code, "answer_preview": final_answer[:100] if final_answer else ""})
        return {}
    except Exception as e:
        logger.error("Unexpected error in guardrails output validation", exc_info=True, extra={"error_type": type(e).__name__, "answer_preview": final_answer[:100] if final_answer else ""})
        return {}

