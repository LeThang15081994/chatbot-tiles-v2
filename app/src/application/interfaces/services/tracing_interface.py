"""
Tracing Service Interface
Abstract interface for observability and tracing service
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any


class ITracingService(ABC):
    """
    Interface for tracing/observability service

    Application layer interface - no infrastructure dependencies.
    Allows Application layer to use tracing without depending on concrete implementations.
    """

    @abstractmethod
    def update_trace(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> None:
        """
        Update current trace with session/user info

        Args:
            session_id: Optional session ID
            user_id: Optional user ID
        """
        pass

    @abstractmethod
    def get_session_history(
        self,
        session_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get chat history for session

        Args:
            session_id: Session ID
            limit: Maximum number of messages to fetch

        Returns:
            List of chat messages with role and content
        """
        pass

    @abstractmethod
    def flush(self) -> None:
        """Flush pending traces"""
        pass

    @abstractmethod
    def get_prompt(
        self,
        name: str,
        label: str = "production",
        type: str = "text"
    ) -> Optional[Any]:
        """
        Get prompt from prompt service

        Args:
            name: Prompt name
            label: Prompt label (production/staging)
            type: Prompt type (text/chat)

        Returns:
            Prompt object or None
        """
        pass

