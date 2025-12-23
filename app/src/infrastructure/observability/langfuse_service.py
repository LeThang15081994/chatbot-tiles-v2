"""
Langfuse Service Implementation
Handles tracing, prompts, and session management
"""
from typing import Optional, List, Dict, Any
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler

from app.src.infrastructure.config.langfuse_settings import LangfuseSettings


class LangfuseService:
    """
    Langfuse service for observability

    Provides:
    - Tracing and logging
    - Prompt management
    - Session tracking
    - User tracking
    """

    def __init__(self, settings: LangfuseSettings):
        """
        Initialize Langfuse service

        Args:
            settings: Langfuse configuration settings
        """
        self.settings = settings
        self.client: Optional[Langfuse] = None
        self.handler: Optional[CallbackHandler] = None
        self._initialize()

    def _initialize(self) -> None:
        """Initialize Langfuse client and handler"""
        try:
            import os

            # Set environment variables for Langfuse
            os.environ["LANGFUSE_PUBLIC_KEY"] = self.settings.LANGFUSE_PUBLIC_KEY
            os.environ["LANGFUSE_SECRET_KEY"] = self.settings.LANGFUSE_SECRET_KEY
            os.environ["LANGFUSE_HOST"] = self.settings.LANGFUSE_HOST
            os.environ["LANGFUSE_TRACING_ENVIRONMENT"] = self.settings.ENVIRONMENT
            os.environ["LANGFUSE_RELEASE"] = self.settings.APP_VERSION

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

