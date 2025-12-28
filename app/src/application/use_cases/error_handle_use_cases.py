"""
Custom Exceptions for RAG Orchestration

Specific exception types for better error handling and debugging.
"""
from typing import Optional, Dict, Any


class RAGOrchestrationError(Exception):
    """Base exception for RAG orchestration errors"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class GuardrailsError(RAGOrchestrationError):
    """Exception raised when guardrails validation fails"""

    def __init__(
        self,
        message: str,
        validation_type: str = "unknown",
        blocked: bool = False,
        details: Optional[Dict[str, Any]] = None
    ):
        self.validation_type = validation_type  # "input" or "output"
        self.blocked = blocked
        super().__init__(
            message=message,
            error_code="GUARDRAILS_ERROR",
            details=details or {}
        )


class GuardrailsServiceError(RAGOrchestrationError):
    """Exception raised when guardrails service is unavailable or fails"""

    def __init__(
        self,
        message: str,
        service_error: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.service_error = service_error
        super().__init__(
            message=message,
            error_code="GUARDRAILS_SERVICE_ERROR",
            details=details or {}
        )


class LLMDecisionError(RAGOrchestrationError):
    """Exception raised when LLM decision node fails"""

    def __init__(
        self,
        message: str,
        llm_response: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.llm_response = llm_response
        super().__init__(
            message=message,
            error_code="LLM_DECISION_ERROR",
            details=details or {}
        )


class JSONParseError(RAGOrchestrationError):
    """Exception raised when JSON parsing fails"""

    def __init__(
        self,
        message: str,
        raw_response: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.raw_response = raw_response
        super().__init__(
            message=message,
            error_code="JSON_PARSE_ERROR",
            details=details or {}
        )


class ToolExecutionError(RAGOrchestrationError):
    """Exception raised when tool execution fails"""

    def __init__(
        self,
        message: str,
        tool_name: Optional[str] = None,
        tool_error: Optional[Exception] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.tool_name = tool_name
        self.tool_error = tool_error
        super().__init__(
            message=message,
            error_code="TOOL_EXECUTION_ERROR",
            details=details or {}
        )


class SearchError(RAGOrchestrationError):
    """Exception raised when search operation fails"""

    def __init__(
        self,
        message: str,
        search_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.search_type = search_type
        super().__init__(
            message=message,
            error_code="SEARCH_ERROR",
            details=details or {}
        )


class AnswerGenerationError(RAGOrchestrationError):
    """Exception raised when answer generation fails"""

    def __init__(
        self,
        message: str,
        generation_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.generation_type = generation_type  # "rag", "direct", "action"
        super().__init__(
            message=message,
            error_code="ANSWER_GENERATION_ERROR",
            details=details or {}
        )


class StateValidationError(RAGOrchestrationError):
    """Exception raised when graph state validation fails"""

    def __init__(
        self,
        message: str,
        missing_fields: Optional[list] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.missing_fields = missing_fields or []
        super().__init__(
            message=message,
            error_code="STATE_VALIDATION_ERROR",
            details=details or {}
        )

