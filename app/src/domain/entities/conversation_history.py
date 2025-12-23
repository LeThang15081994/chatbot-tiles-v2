"""
Conversation History Entity
Manages conversation history with summarization and truncation
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4


@dataclass
class ConversationHistory:
    """
    Conversation history entity

    Manages chat history with smart truncation and summarization.
    Handles memory management for long conversations.
    """

    history_id: str = field(default_factory=lambda: str(uuid4()))
    session_id: Optional[str] = None
    messages: List[Dict[str, Any]] = field(default_factory=list)
    summary: Optional[str] = None
    max_messages: int = 20
    summarization_threshold: int = 12
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None) -> None:
        """
        Add a message to history

        Args:
            role: Message role (user/assistant/system)
            content: Message content
            metadata: Optional metadata
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.messages.append(message)
        self.updated_at = datetime.now()

        # Auto-truncate if exceeds max
        if len(self.messages) > self.max_messages:
            self._truncate_old_messages()

    def add_user_message(self, content: str, metadata: Optional[Dict] = None) -> None:
        """Add user message"""
        self.add_message("user", content, metadata)

    def add_assistant_message(self, content: str, metadata: Optional[Dict] = None) -> None:
        """Add assistant message"""
        self.add_message("assistant", content, metadata)

    def add_system_message(self, content: str, metadata: Optional[Dict] = None) -> None:
        """Add system message"""
        self.add_message("system", content, metadata)

    def get_recent_messages(self, count: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent messages

        Args:
            count: Number of recent messages

        Returns:
            List of recent messages
        """
        return self.messages[-count:] if len(self.messages) > count else self.messages

    def get_messages_for_llm(self) -> List[Dict[str, str]]:
        """
        Get messages formatted for LLM

        Returns:
            List of messages with role and content only
        """
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in self.messages
        ]

    def format_as_text(self, max_messages: Optional[int] = None) -> str:
        """
        Format history as text

        Args:
            max_messages: Maximum number of messages to include

        Returns:
            Formatted text
        """
        messages_to_format = self.messages
        if max_messages:
            messages_to_format = self.messages[-max_messages:]

        lines = []
        for msg in messages_to_format:
            role = msg["role"].capitalize()
            content = msg["content"]
            lines.append(f"{role}: {content}")

        return "\n".join(lines)

    def count_messages(self) -> int:
        """Get total message count"""
        return len(self.messages)

    def count_tokens_estimate(self) -> int:
        """
        Estimate token count (rough approximation)

        Returns:
            Estimated token count
        """
        total_chars = sum(len(msg["content"]) for msg in self.messages)
        # Rough estimate: 1 token ≈ 4 characters
        return total_chars // 4

    def needs_summarization(self) -> bool:
        """
        Check if history needs summarization

        Returns:
            True if exceeds threshold
        """
        return len(self.messages) >= self.summarization_threshold

    def set_summary(self, summary: str) -> None:
        """
        Set conversation summary

        Args:
            summary: Summary text
        """
        self.summary = summary
        self.updated_at = datetime.now()

    def _truncate_old_messages(self, keep_count: Optional[int] = None) -> int:
        """
        Truncate old messages

        Args:
            keep_count: Number of messages to keep (default: max_messages)

        Returns:
            Number of messages removed
        """
        keep = keep_count or self.max_messages
        if len(self.messages) <= keep:
            return 0

        removed_count = len(self.messages) - keep
        self.messages = self.messages[-keep:]
        self.updated_at = datetime.now()

        return removed_count

    def clear_history(self) -> int:
        """
        Clear all history

        Returns:
            Number of messages cleared
        """
        count = len(self.messages)
        self.messages = []
        self.summary = None
        self.updated_at = datetime.now()
        return count

    def get_last_user_message(self) -> Optional[Dict[str, Any]]:
        """
        Get last user message

        Returns:
            Last user message or None
        """
        for msg in reversed(self.messages):
            if msg["role"] == "user":
                return msg
        return None

    def get_last_assistant_message(self) -> Optional[Dict[str, Any]]:
        """
        Get last assistant message

        Returns:
            Last assistant message or None
        """
        for msg in reversed(self.messages):
            if msg["role"] == "assistant":
                return msg
        return None

    def get_conversation_context(
        self,
        include_summary: bool = True,
        max_recent: int = 8
    ) -> str:
        """
        Get conversation context for RAG

        Args:
            include_summary: Include summary if available
            max_recent: Maximum recent messages to include

        Returns:
            Formatted context string
        """
        parts = []

        # Add summary if available
        if include_summary and self.summary:
            parts.append(f"[Previous Conversation Summary]\n{self.summary}\n")

        # Add recent messages
        recent_messages = self.get_recent_messages(max_recent)
        if recent_messages:
            parts.append("[Recent Conversation]")
            for msg in recent_messages:
                role = msg["role"].capitalize()
                content = msg["content"]
                parts.append(f"{role}: {content}")

        return "\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary

        Returns:
            Dictionary representation
        """
        return {
            "history_id": self.history_id,
            "session_id": self.session_id,
            "messages": self.messages,
            "summary": self.summary,
            "message_count": len(self.messages),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationHistory':
        """
        Create from dictionary

        Args:
            data: Dictionary data

        Returns:
            ConversationHistory instance
        """
        return cls(
            history_id=data.get("history_id", str(uuid4())),
            session_id=data.get("session_id"),
            messages=data.get("messages", []),
            summary=data.get("summary"),
            metadata=data.get("metadata", {})
        )

    def __repr__(self) -> str:
        return (
            f"ConversationHistory("
            f"id={self.history_id[:8]}, "
            f"session={self.session_id[:8] if self.session_id else 'None'}, "
            f"messages={len(self.messages)}, "
            f"has_summary={bool(self.summary)}"
            f")"
        )

