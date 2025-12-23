"""
Conversation Manager Domain Service
Manages conversation history, summarization, and memory
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.src.domain.entities.message import Message, MessageRole
from app.src.domain.entities.conversation_history import ConversationHistory
from app.src.domain.entities.chat_session import ChatSession


class ConversationManagerService:
    """
    Conversation manager domain service

    Manages conversation state, history, and memory.
    Handles summarization, truncation, and context window management.
    """

    def __init__(
        self,
        max_messages: int = 20,
        summarization_threshold: int = 12,
        max_context_tokens: int = 4000,
        enable_auto_summarization: bool = True
    ):
        """
        Initialize conversation manager

        Args:
            max_messages: Maximum messages to keep in memory
            summarization_threshold: Trigger summarization at this count
            max_context_tokens: Maximum context tokens
            enable_auto_summarization: Enable automatic summarization
        """
        self.max_messages = max_messages
        self.summarization_threshold = summarization_threshold
        self.max_context_tokens = max_context_tokens
        self.enable_auto_summarization = enable_auto_summarization

    def add_message_to_session(
        self,
        session: ChatSession,
        message: Message
    ) -> ChatSession:
        """
        Add message to chat session

        Args:
            session: Chat session
            message: Message to add

        Returns:
            Updated session
        """
        session.add_message(message)

        # Check if we need to truncate
        if len(session.messages) > self.max_messages:
            removed = session.clear_old_messages(self.max_messages)
            if removed > 0:
                # Could trigger summarization here
                pass

        return session

    def create_conversation_history(
        self,
        session: ChatSession,
        max_messages: Optional[int] = None
    ) -> ConversationHistory:
        """
        Create ConversationHistory from ChatSession

        Args:
            session: Chat session
            max_messages: Maximum messages to include

        Returns:
            ConversationHistory instance
        """
        messages_data = []
        messages_to_use = session.get_recent_messages(
            max_messages or self.max_messages
        )

        for msg in messages_to_use:
            messages_data.append({
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "metadata": msg.metadata
            })

        return ConversationHistory(
            session_id=session.session_id,
            messages=messages_data,
            max_messages=self.max_messages,
            summarization_threshold=self.summarization_threshold
        )

    def should_summarize(
        self,
        history: ConversationHistory
    ) -> bool:
        """
        Check if conversation should be summarized

        Args:
            history: Conversation history

        Returns:
            True if should summarize
        """
        if not self.enable_auto_summarization:
            return False

        return history.needs_summarization()

    def prepare_messages_for_summarization(
        self,
        history: ConversationHistory,
        keep_recent: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Prepare messages for summarization

        Args:
            history: Conversation history
            keep_recent: Number of recent messages to keep unsummarized

        Returns:
            List of messages to summarize
        """
        total_messages = history.count_messages()
        if total_messages <= keep_recent:
            return []

        # Get old messages to summarize
        messages_to_summarize = history.messages[:-keep_recent]
        return messages_to_summarize

    def apply_summary(
        self,
        history: ConversationHistory,
        summary: str,
        keep_recent: int = 4
    ) -> ConversationHistory:
        """
        Apply summary to conversation history

        Args:
            history: Conversation history
            summary: Summary text
            keep_recent: Number of recent messages to keep

        Returns:
            Updated history with summary
        """
        # Keep recent messages
        recent_messages = history.get_recent_messages(keep_recent)

        # Create new history with summary
        new_messages = [
            {
                "role": "system",
                "content": f"Previous conversation summary: {summary}",
                "timestamp": datetime.now().isoformat(),
                "metadata": {"is_summary": True}
            }
        ] + recent_messages

        return ConversationHistory(
            history_id=history.history_id,
            session_id=history.session_id,
            messages=new_messages,
            summary=summary,
            max_messages=self.max_messages,
            summarization_threshold=self.summarization_threshold,
            metadata=history.metadata
        )

    def format_for_llm(
        self,
        history: ConversationHistory,
        include_summary: bool = True
    ) -> List[Dict[str, str]]:
        """
        Format history for LLM consumption

        Args:
            history: Conversation history
            include_summary: Include summary if available

        Returns:
            List of formatted messages
        """
        messages = []

        # Add summary as system message if available
        if include_summary and history.summary:
            messages.append({
                "role": "system",
                "content": f"Previous conversation summary: {history.summary}"
            })

        # Add regular messages
        messages.extend(history.get_messages_for_llm())

        return messages

    def truncate_to_token_limit(
        self,
        history: ConversationHistory,
        max_tokens: Optional[int] = None
    ) -> ConversationHistory:
        """
        Truncate history to fit token limit

        Args:
            history: Conversation history
            max_tokens: Maximum tokens (uses default if None)

        Returns:
            Truncated history
        """
        limit = max_tokens or self.max_context_tokens
        current_tokens = history.count_tokens_estimate()

        if current_tokens <= limit:
            return history

        # Remove old messages until under limit
        messages = history.messages.copy()
        while len(messages) > 1:
            # Always keep at least 1 message
            messages.pop(0)

            # Recalculate tokens
            temp_history = ConversationHistory(
                session_id=history.session_id,
                messages=messages,
                summary=history.summary
            )
            if temp_history.count_tokens_estimate() <= limit:
                return temp_history

        return history

    def get_conversation_context(
        self,
        history: ConversationHistory,
        max_messages: Optional[int] = None
    ) -> str:
        """
        Get conversation context as text

        Args:
            history: Conversation history
            max_messages: Maximum messages to include

        Returns:
            Formatted context string
        """
        return history.get_conversation_context(
            include_summary=True,
            max_recent=max_messages or 8
        )

    def extract_user_queries(
        self,
        history: ConversationHistory
    ) -> List[str]:
        """
        Extract all user queries from history

        Args:
            history: Conversation history

        Returns:
            List of user queries
        """
        queries = []
        for msg in history.messages:
            if msg.get("role") == "user":
                queries.append(msg.get("content", ""))
        return queries

    def extract_assistant_responses(
        self,
        history: ConversationHistory
    ) -> List[str]:
        """
        Extract all assistant responses from history

        Args:
            history: Conversation history

        Returns:
            List of assistant responses
        """
        responses = []
        for msg in history.messages:
            if msg.get("role") == "assistant":
                responses.append(msg.get("content", ""))
        return responses

    def get_last_interaction(
        self,
        history: ConversationHistory
    ) -> Optional[Dict[str, str]]:
        """
        Get last user-assistant interaction

        Args:
            history: Conversation history

        Returns:
            Dictionary with user query and assistant response
        """
        last_user = history.get_last_user_message()
        last_assistant = history.get_last_assistant_message()

        if not last_user or not last_assistant:
            return None

        return {
            "user": last_user.get("content", ""),
            "assistant": last_assistant.get("content", "")
        }

    def calculate_conversation_stats(
        self,
        history: ConversationHistory
    ) -> Dict[str, Any]:
        """
        Calculate conversation statistics

        Args:
            history: Conversation history

        Returns:
            Dictionary with statistics
        """
        user_messages = [m for m in history.messages if m.get("role") == "user"]
        assistant_messages = [m for m in history.messages if m.get("role") == "assistant"]

        return {
            "total_messages": history.count_messages(),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "estimated_tokens": history.count_tokens_estimate(),
            "has_summary": bool(history.summary),
            "needs_summarization": history.needs_summarization(),
            "created_at": history.created_at.isoformat(),
            "updated_at": history.updated_at.isoformat()
        }

    def merge_histories(
        self,
        history1: ConversationHistory,
        history2: ConversationHistory
    ) -> ConversationHistory:
        """
        Merge two conversation histories

        Args:
            history1: First history
            history2: Second history

        Returns:
            Merged history
        """
        all_messages = history1.messages + history2.messages

        # Sort by timestamp
        all_messages.sort(
            key=lambda m: m.get("timestamp", datetime.now().isoformat())
        )

        # Limit to max messages
        if len(all_messages) > self.max_messages:
            all_messages = all_messages[-self.max_messages:]

        return ConversationHistory(
            session_id=history1.session_id or history2.session_id,
            messages=all_messages,
            max_messages=self.max_messages,
            summarization_threshold=self.summarization_threshold
        )

