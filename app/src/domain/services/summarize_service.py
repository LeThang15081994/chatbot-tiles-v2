"""
Summarization Domain Service
Summarizes long chat history to manage context window
"""
from typing import List, Dict, Optional, Any


class SummarizeService:
    """
    Summarization service for chat history

    Summarizes old messages to keep conversation context manageable.
    Similar to code cũ: chatbot-ceramic-tiles/chat-backend/src/services/domain/summarize.py
    """

    def __init__(
        self,
        llm_service: Optional[Any] = None,
        keep_last: int = 4
    ):
        """
        Initialize summarization service

        Args:
            llm_service: LLM service for generating summaries (ILLMRepository interface)
            keep_last: Number of recent messages to keep unsummarized
        """
        self.llm_service = llm_service
        self.keep_last = keep_last

    async def summarize_and_truncate_history(
        self,
        chat_history: List[Dict[str, str]],
        session_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Summarize old messages and keep recent ones (giống code cũ)

        Summary 4 messages cũ nhất và giữ lại phần còn lại

        Args:
            chat_history: Full chat history
            session_id: Optional session ID for tracing
            user_id: Optional user ID for tracing

        Returns:
            Summarized history with recent messages kept
        """
        # If history is short enough, return as is
        if len(chat_history) <= self.keep_last:
            return chat_history

        try:
            # Lấy keep_last messages cũ nhất để summary
            old_messages = chat_history[:self.keep_last]
            remaining_messages = chat_history[self.keep_last:]

            # Tạo summary từ old messages (giống code cũ)
            old_conversation = "\n".join(
                [
                    f"{msg.get('role', 'user').capitalize()}: {msg.get('content', '')}"
                    for msg in old_messages
                ]
            )

            summary_prompt = f"""Summarize this conversation in English, keeping key information (in 2-3 sentences):
{old_conversation}"""

            # Call LLM để summary (giống code cũ)
            if self.llm_service:
                try:
                    # Use generate_response method (from ILLMService interface)
                    # Create messages as dict (Domain layer doesn't import Application DTOs)
                    summary_messages = [
                        {"role": "system", "content": "You are a helpful assistant that summarizes conversations concisely."},
                        {"role": "user", "content": summary_prompt}
                    ]
                    summary_response = await self.llm_service.generate_response(
                        messages=summary_messages,
                        temperature=0.3,
                        max_tokens=150
                    )
                    # Extract content from response (should be string)
                    if isinstance(summary_response, str):
                        summary_content = summary_response
                    elif isinstance(summary_response, dict):
                        summary_content = summary_response.get("content", "") or summary_response.get("answer", "") or summary_response.get("response", "")
                    else:
                        summary_content = str(summary_response)
                except Exception as e:
                    print(f"Error calling LLM for summarization: {e}")
                    # Fallback: simple truncation
                    summary_content = f"Previous conversation about: {old_conversation[:100]}..."
            else:
                # Fallback: simple truncation
                summary_content = f"Previous conversation about: {old_conversation[:100]}..."

            # Tạo history mới: summary + remaining messages (giống code cũ)
            summarized_history = [
                {
                    "role": "system",
                    "content": f"Previous conversation summary: {summary_content}",
                }
            ] + remaining_messages

            return summarized_history

        except Exception as e:
            # Fallback: chỉ lấy recent messages (giống code cũ)
            print(f"Error summarizing history: {e}")
            return chat_history[-self.keep_last:]

