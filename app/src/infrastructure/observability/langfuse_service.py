"""
Langfuse Service Implementation
Handles tracing, prompts, session management, and metrics collection
"""
import time
import logging
from typing import Optional, List, Dict, Any
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

from app.src.infrastructure.config.settings import LangfuseSettings, Settings, settings

logger = logging.getLogger(__name__)


class LangfuseMetrics:
    """
    Metrics collection for Langfuse

    Tracks:
    - Request counts
    - Response times
    - Error rates
    - Token usage
    - Cache hit rates
    """

    def __init__(self):
        """Initialize metrics"""
        self.request_count = 0
        self.error_count = 0
        self.total_response_time = 0.0
        self.total_tokens = 0
        self.cache_hits = 0
        self.cache_misses = 0

    def record_request(self, response_time: float, tokens: int = 0, cache_hit: bool = False):
        """
        Record a request metric

        Args:
            response_time: Response time in seconds
            tokens: Number of tokens used
            cache_hit: Whether cache was hit
        """
        self.request_count += 1
        self.total_response_time += response_time
        self.total_tokens += tokens
        if cache_hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

    def record_error(self):
        """Record an error"""
        self.error_count += 1

    def get_stats(self) -> Dict[str, Any]:
        """
        Get current metrics statistics

        Returns:
            Dictionary with metrics
        """
        avg_response_time = (
            self.total_response_time / self.request_count
            if self.request_count > 0
            else 0.0
        )
        error_rate = (
            self.error_count / self.request_count
            if self.request_count > 0
            else 0.0
        )
        cache_hit_rate = (
            self.cache_hits / (self.cache_hits + self.cache_misses)
            if (self.cache_hits + self.cache_misses) > 0
            else 0.0
        )

        return {
            "request_count": self.request_count,
            "error_count": self.error_count,
            "error_rate": error_rate,
            "avg_response_time_ms": avg_response_time * 1000,
            "total_tokens": self.total_tokens,
            "avg_tokens_per_request": (
                self.total_tokens / self.request_count
                if self.request_count > 0
                else 0
            ),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": cache_hit_rate
        }

    def reset(self):
        """Reset all metrics"""
        self.request_count = 0
        self.error_count = 0
        self.total_response_time = 0.0
        self.total_tokens = 0
        self.cache_hits = 0
        self.cache_misses = 0


class LangfuseService:
    """
    Langfuse service for observability

    Provides:
    - Tracing and logging
    - Prompt management
    - Session tracking
    - User tracking
    - Metrics collection
    """

    def __init__(self, langfuse_settings: LangfuseSettings):
        """
        Initialize Langfuse service

        Args:
            langfuse_settings: Langfuse settings instance
        """
        self.langfuse_settings = langfuse_settings
        self.client: Optional[Langfuse] = None
        self.handler: Optional[CallbackHandler] = None
        self.metrics = LangfuseMetrics()
        self._initialize()

    def _initialize(self) -> None:
        # Skip initialization if Langfuse keys are not provided
        if not self.langfuse_settings.LANGFUSE_PUBLIC_KEY or not self.langfuse_settings.LANGFUSE_SECRET_KEY:
            return

        try:
            import os

            # Set environment variables for Langfuse
            os.environ["LANGFUSE_PUBLIC_KEY"] = self.langfuse_settings.LANGFUSE_PUBLIC_KEY
            os.environ["LANGFUSE_SECRET_KEY"] = self.langfuse_settings.LANGFUSE_SECRET_KEY
            os.environ["LANGFUSE_HOST"] = self.langfuse_settings.LANGFUSE_HOST
            os.environ["LANGFUSE_TRACING_ENVIRONMENT"] = self.langfuse_settings.LANGFUSE_ENVIRONMENT
            # Get APP_VERSION from global settings
            app_version = settings.APP_VERSION
            os.environ["LANGFUSE_RELEASE"] = app_version

            # Initialize client
            from langfuse import get_client
            self.client = get_client()

            # Initialize callback handler
            self.handler = CallbackHandler()

        except Exception as e:
            raise RuntimeError(f"Failed to initialize Langfuse: {e}")

    def get_callback_handler(self) -> CallbackHandler:
        """Get Langfuse callback handler for LangChain"""
        if not self.handler:
            raise RuntimeError("Langfuse handler not initialized")
        return self.handler

    def get_prompt(
        self,
        name: str,
        label: str = "production",
        type: str = "text"
    ) -> Optional[Any]:
        """
        Get prompt from Langfuse dashboard

        Args:
            name: Prompt name
            label: Prompt label (production/staging)
            type: Prompt type (text/chat)

        Returns:
            Prompt object or None
        """
        try:
            if not self.client:
                return None

            return self.client.get_prompt(name, label=label, type=type)

        except Exception:
            return None

    def get_session_history(
        self,
        session_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get chat history for session from Langfuse

        Args:
            session_id: Session ID
            limit: Maximum number of traces to fetch

        Returns:
            List of chat messages
        """
        try:
            if not self.client:
                return []

            # Fetch traces for session
            traces = self.client.api.trace.list(
                session_id=session_id,
                limit=limit
            )

            # Sort by timestamp
            sorted_traces = sorted(
                traces.data,
                key=lambda x: x.timestamp
            )

            # Extract chat messages
            chat_history = []
            for trace in sorted_traces:
                user_question = ""
                ai_answer = ""

                if isinstance(trace.input, dict):
                    user_question = trace.input.get("question", "")

                if isinstance(trace.output, str):
                    ai_answer = trace.output
                elif isinstance(trace.output, dict):
                    ai_answer = trace.output.get("content", "") or trace.output.get("response", "")

                if user_question and ai_answer:
                    chat_history.extend([
                        {"role": "user", "content": user_question},
                        {"role": "assistant", "content": ai_answer},
                    ])

            # Return recent messages only
            return chat_history[-12:]

        except Exception:
            return []

    def update_trace(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> None:
        """Update current trace with session/user info"""
        try:
            if not self.client:
                return

            if session_id:
                self.client.update_current_trace(session_id=session_id)
            if user_id:
                self.client.update_current_trace(user_id=user_id)

        except Exception:
            pass

    def flush(self) -> None:
        """Flush pending traces"""
        try:
            if self.client:
                self.client.flush()
        except Exception:
            pass

    def health_check(self) -> bool:
        """Check Langfuse health"""
        try:
            return self.client is not None and self.handler is not None
        except Exception:
            return False

    def track_span(
        self,
        name: str,
        input: Optional[Dict[str, Any]] = None,
        output: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
        level: str = "DEFAULT"
    ) -> Optional[str]:
        """
        Track a span in Langfuse

        Args:
            name: Span name
            input: Span input
            output: Span output
            metadata: Additional metadata
            level: Span level (DEFAULT, DEBUG, INFO, WARNING, ERROR)

        Returns:
            Span ID or None
        """
        try:
            if not self.client:
                return None

            span = self.client.span(
                name=name,
                input=input,
                output=output,
                metadata=metadata,
                level=level
            )
            return span.id if span else None
        except Exception as e:
            logger.warning(f"Failed to track span: {e}", extra={"span_name": name})
            return None

    def track_generation(
        self,
        name: str,
        model: str,
        input: Optional[Any] = None,
        output: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
        usage: Optional[Dict[str, int]] = None
    ) -> Optional[str]:
        """
        Track LLM generation in Langfuse

        Args:
            name: Generation name
            model: Model name
            input: Generation input
            output: Generation output
            metadata: Additional metadata
            usage: Token usage (prompt_tokens, completion_tokens, total_tokens)

        Returns:
            Generation ID or None
        """
        try:
            if not self.client:
                return None

            generation = self.client.generation(
                name=name,
                model=model,
                input=input,
                output=output,
                metadata=metadata,
                usage=usage
            )

            # Record metrics
            if usage:
                tokens = usage.get("total_tokens", 0)
                self.metrics.record_request(
                    response_time=0.0,  # Will be updated by caller
                    tokens=tokens
                )

            return generation.id if generation else None
        except Exception as e:
            logger.warning(f"Failed to track generation: {e}", extra={"generation_name": name})
            return None

    def track_score(
        self,
        name: str,
        value: float,
        comment: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Track a score in Langfuse

        Args:
            name: Score name
            value: Score value
            comment: Optional comment
            trace_id: Optional trace ID to associate with

        Returns:
            Score ID or None
        """
        try:
            if not self.client:
                return None

            score = self.client.score(
                name=name,
                value=value,
                comment=comment,
                trace_id=trace_id
            )
            return score.id if score else None
        except Exception as e:
            logger.warning(f"Failed to track score: {e}", extra={"score_name": name})
            return None

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics

        Returns:
            Dictionary with metrics statistics
        """
        return self.metrics.get_stats()

    def reset_metrics(self):
        """Reset metrics"""
        self.metrics.reset()

