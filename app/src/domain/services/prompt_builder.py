"""
Prompt Builder Domain Service
Builds prompts for LLM from context and templates
"""
import logging
from typing import List, Optional, Dict, Any
from app.src.domain.entities.document import Document
from app.src.domain.entities.message import Message, MessageRole
from app.src.domain.value_objects.context import RAGContext
from app.src.domain.value_objects.prompt import PromptTemplate
from app.src.infrastructure.config.settings import langfuse_settings

logger = logging.getLogger(__name__)


class PromptLoadError(Exception):
    """Raised when required prompts cannot be loaded from Langfuse"""
    pass


class PromptBuilderService:
    """
    Prompt builder domain service

    Responsible for building prompts for LLM generation.
    Handles context formatting, history integration, and template rendering.
    """

    @staticmethod
    def _get_prompt_label_from_environment() -> str:
        """
        Map APP_ENVIRONMENT to Langfuse prompt label

        Returns:
            Prompt label: "production" for production, "staging" for staging/development
        """
        return langfuse_settings.LANGFUSE_ENVIRONMENT

    def __init__(
        self,
        system_prompt: Optional[str] = None,
        include_context_header: bool = True,
        include_history_header: bool = True,
        max_history_messages: int = 8,
        langfuse_service: Optional[Any] = None
    ):
        """
        Initialize prompt builder

        Args:
            system_prompt: System prompt template
            include_context_header: Include context header
            include_history_header: Include history header
            max_history_messages: Maximum history messages to include
            langfuse_service: Optional LangfuseService for loading prompts from Langfuse
        """
        self.langfuse_service = langfuse_service
        # Get prompt label based on environment
        self.prompt_label = self._get_prompt_label_from_environment()
        logger.info(
            f"PromptBuilderService initialized with APP_ENVIRONMENT='{langfuse_settings.LANGFUSE_ENVIRONMENT}', "
            f"using Langfuse prompt label='{self.prompt_label}'"
        )

        if not self.langfuse_service:
            raise PromptLoadError(
                "LangfuseService is required but not provided. "
                "Prompts must be loaded from Langfuse Dashboard."
            )

        # Load userinput_service prompt (used for tool calling decision - system prompt)
        try:
            self.prompt_userinput = self.langfuse_service.get_prompt(
                "userinput_service",
                label=self.prompt_label,
                type="text"
            )
            if not self.prompt_userinput:
                raise PromptLoadError(
                    f"Failed to load 'userinput_service' prompt from Langfuse. "
                    f"This prompt is required for tool calling decisions (system prompt). "
                    f"Please ensure the prompt exists in Langfuse Dashboard with label '{self.prompt_label}'."
                )
        except Exception as e:
            if isinstance(e, PromptLoadError):
                raise
            raise PromptLoadError(
                f"Failed to load 'userinput_service' prompt from Langfuse: {str(e)}. "
                "This prompt is required for tool calling decisions."
            )

        # Load RAG prompt for company_info tool
        try:
            self.prompt_rag_company_info = self.langfuse_service.get_prompt(
                "rag_company_info",
                label=self.prompt_label,
                type="text"
            )
            if not self.prompt_rag_company_info:
                raise PromptLoadError(
                    f"Failed to load 'rag_company_info' prompt from Langfuse. "
                    f"This prompt is required for RAG generation when using search_company_info tool. "
                    f"Please ensure the prompt exists in Langfuse Dashboard with label '{self.prompt_label}'."
                )
        except Exception as e:
            if isinstance(e, PromptLoadError):
                raise
            raise PromptLoadError(
                f"Failed to load 'rag_company_info' prompt from Langfuse: {str(e)}. "
                "This prompt is required for RAG generation with search_company_info tool."
            )

        # Load RAG prompt for collection_info tool
        try:
            self.prompt_rag_collection_info = self.langfuse_service.get_prompt(
                "rag_collection_info",
                label=self.prompt_label,
                type="text"
            )
            if not self.prompt_rag_collection_info:
                raise PromptLoadError(
                    f"Failed to load 'rag_collection_info' prompt from Langfuse. "
                    f"This prompt is required for RAG generation when using search_collection_info tool. "
                    f"Please ensure the prompt exists in Langfuse Dashboard with label '{self.prompt_label}'."
                )
        except Exception as e:
            if isinstance(e, PromptLoadError):
                raise
            raise PromptLoadError(
                f"Failed to load 'rag_collection_info' prompt from Langfuse: {str(e)}. "
                "This prompt is required for RAG generation with search_collection_info tool."
            )

        # Load RAG prompt for products tool
        try:
            self.prompt_rag_products = self.langfuse_service.get_prompt(
                "rag_products",
                label=self.prompt_label,
                type="text"
            )
            if not self.prompt_rag_products:
                raise PromptLoadError(
                    f"Failed to load 'rag_products' prompt from Langfuse. "
                    f"This prompt is required for RAG generation when using search_products tool. "
                    f"Please ensure the prompt exists in Langfuse Dashboard with label '{self.prompt_label}'."
                )
        except Exception as e:
            if isinstance(e, PromptLoadError):
                raise
            raise PromptLoadError(
                f"Failed to load 'rag_products' prompt from Langfuse: {str(e)}. "
                "This prompt is required for RAG generation with search_products tool."
            )

        # Load action response prompt (for formatting responses after action tools like add_to_cart)
        try:
            self.prompt_action_response = self.langfuse_service.get_prompt(
                "action_response_prompt",
                label=self.prompt_label,
                type="text"
            )
            if not self.prompt_action_response:
                raise PromptLoadError(
                    f"Failed to load 'action_response_prompt' prompt from Langfuse. "
                    f"This prompt is required for formatting responses after action tools (like add_to_cart). "
                    f"Please ensure the prompt exists in Langfuse Dashboard with label '{self.prompt_label}'."
                )
        except Exception as e:
            if isinstance(e, PromptLoadError):
                raise
            raise PromptLoadError(
                f"Failed to load 'action_response_prompt' prompt from Langfuse: {str(e)}. "
                "This prompt is required for formatting responses after action tools."
            )

        # Use system prompt (provided or default)
        self.system_prompt = system_prompt or self._get_default_system_prompt()
        self.include_context_header = include_context_header
        self.include_history_header = include_history_header
        self.max_history_messages = max_history_messages

    def _get_default_system_prompt(self) -> str:
        """Get default system prompt"""
        return """You are a helpful AI assistant specialized in answering questions based on provided context.
Your responses should be:
- Accurate and based on the provided context
- Clear and well-structured
- Helpful and informative
- Professional in tone

If the context doesn't contain enough information to answer the question, acknowledge this limitation."""


    def build_initial_messages(
        self,
        user_query: str,
        system_prompt: Optional[str] = None,
        use_tool_calling: bool = True,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, str]]:
        """
        Build initial messages for LLM (system + user)
        Uses Langfuse prompt_userinput (REQUIRED for tool calling)

        The userinput_service prompt is responsible for deciding which tool to call.
        It guides the LLM to choose between search_company_info and search_collection_info.

        Args:
            user_query: User's question
            system_prompt: Optional system prompt override
            use_tool_calling: Whether to use tool calling system prompt
            chat_history: Optional chat history for prompt formatting

        Returns:
            List of message dictionaries with role and content

        Raises:
            PromptLoadError: If prompt_userinput is not loaded from Langfuse when use_tool_calling=True
        """
        # If system_prompt is explicitly provided, use it
        if system_prompt:
            return [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ]

        # For tool calling, MUST use Langfuse prompt_userinput
        if use_tool_calling:
            if not self.prompt_userinput:
                raise PromptLoadError(
                    "userinput_service prompt is not loaded from Langfuse. "
                    "This prompt is REQUIRED for tool calling decisions. "
                    "It guides the LLM to choose between search_company_info and search_collection_info."
                )

            try:
                formatted_history = "\n".join(
                    f"{m['role'].capitalize()}: {m['content']}" for m in chat_history
                ) if chat_history else ""

                if hasattr(self.prompt_userinput, 'get_langchain_prompt'):
                    # Langfuse prompt object with get_langchain_prompt method
                    prompt_template = self.prompt_userinput.get_langchain_prompt(
                        question=user_query,
                        chat_history=formatted_history
                    )
                    return [
                        {"role": "system", "content": prompt_template}
                    ]
                elif hasattr(self.prompt_userinput, 'prompt'):
                    # Direct prompt content - format with variables
                    prompt_template = self.prompt_userinput.prompt
                    variables = {
                        "question": user_query,
                        "query": user_query,
                        "chat_history": formatted_history,
                    }
                    formatted_prompt = prompt_template
                    for key, value in variables.items():
                        formatted_prompt = formatted_prompt.replace(f"{{{key}}}", str(value))
                    return [
                        {"role": "system", "content": formatted_prompt}
                    ]
                elif isinstance(self.prompt_userinput, str):
                    # String prompt
                    prompt_template = self.prompt_userinput
                    variables = {
                        "question": user_query,
                        "query": user_query,
                        "chat_history": formatted_history,
                    }
                    formatted_prompt = prompt_template
                    for key, value in variables.items():
                        formatted_prompt = formatted_prompt.replace(f"{{{key}}}", str(value))
                    return [
                        {"role": "system", "content": formatted_prompt}
                    ]
                else:
                    raise PromptLoadError(
                        "Unable to extract prompt content from Langfuse prompt_userinput object. "
                        "Please check the prompt format in Langfuse Dashboard."
                    )
            except PromptLoadError:
                raise
            except Exception as e:
                raise PromptLoadError(
                    f"Failed to format userinput_service prompt from Langfuse: {str(e)}"
                )

        # For non-tool calling, use default system prompt
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_query}
        ]

    def build_action_response_prompt(
        self,
        query: str,
        chat_history: Optional[List[Message]] = None
    ) -> str:
        """
        Build prompt for formatting responses after action tools (like add_to_cart)

        This prompt guides the LLM to format a friendly, user-facing response
        based on the tool result (success or failure).

        Args:
            query: Original user query
            chat_history: Optional chat history

        Returns:
            Formatted prompt string for action response formatting
        """
        if not self.prompt_action_response:
            raise PromptLoadError(
                "action_response_prompt prompt is not loaded from Langfuse. "
                "This prompt is REQUIRED for formatting responses after action tools."
            )

        try:
            # Format chat history if available
            history_str = ""
            if chat_history:
                history_parts = []
                for msg in chat_history[-self.max_history_messages:]:
                    role = "User" if msg.role == MessageRole.USER else "Assistant"
                    history_parts.append(f"{role}: {msg.content}")
                history_str = "\n".join(history_parts)

            # Format the action_response prompt
            # The prompt should contain placeholders for {query} and optionally {chat_history}
            prompt = self.prompt_action_response
            if "{query}" in prompt:
                prompt = prompt.replace("{query}", query)
            if "{chat_history}" in prompt and history_str:
                prompt = prompt.replace("{chat_history}", history_str)
            elif "{chat_history}" in prompt:
                prompt = prompt.replace("{chat_history}", "No previous conversation history.")

            return prompt

        except Exception as e:
            raise PromptLoadError(
                f"Failed to format action_response_prompt prompt from Langfuse: {str(e)}"
            )

    def build_rag_prompt(
        self,
        query: str,
        context: RAGContext,
        chat_history: Optional[List[Message]] = None,
        template: Optional[PromptTemplate] = None,
        intent: Optional[str] = None,
        tool_name: Optional[str] = None  # Deprecated: use intent instead
    ) -> str:
        """
        Build RAG prompt with context and history
        Uses Langfuse RAG prompt based on INTENT (not tool_name):
        - company_info -> rag_company_info
        - collection_info -> rag_collection_info
        - products -> rag_products

        Args:
            query: User query
            context: RAG context
            chat_history: Chat history
            template: Optional custom template
            intent: Intent for prompt selection ("company_info", "collection_info", "products")
            tool_name: Deprecated - kept for backward compatibility, use intent instead

        Returns:
            Formatted prompt string

        Raises:
            PromptLoadError: If required prompt is not loaded from Langfuse
        """
        if template:
            return self._build_from_template(template, query, context, chat_history)

        # Select the appropriate RAG prompt based on INTENT (not tool_name)
        # Backward compatibility: if intent not provided, try to infer from tool_name
        if not intent and tool_name:
            if tool_name == "search_company_info":
                intent = "company_info"
            elif tool_name == "search_collection_info":
                intent = "collection_info"
            elif tool_name == "search_products":
                intent = "products"

        # Map intent to prompt
        if intent == "company_info":
            prompt_rag = self.prompt_rag_company_info
            prompt_name = "rag_company_info"
        elif intent == "collection_info":
            prompt_rag = self.prompt_rag_collection_info
            prompt_name = "rag_collection_info"
        elif intent == "products":
            prompt_rag = self.prompt_rag_products
            prompt_name = "rag_products"
        else:
            # Default to company_info if intent not specified
            prompt_rag = self.prompt_rag_company_info
            prompt_name = "rag_company_info"
            intent = "company_info"

        if not prompt_rag:
            raise PromptLoadError(
                f"{prompt_name} prompt is not loaded from Langfuse. "
                f"This prompt is REQUIRED for RAG generation when using {tool_name or 'default'} tool."
            )

        try:
            formatted_history = "\n".join(
                f"{msg.role.value.capitalize()}: {msg.content}" for msg in chat_history
            ) if chat_history else ""

            context_str = context.format_for_llm() if context.has_documents() else ""

            if hasattr(prompt_rag, 'get_langchain_prompt'):
                # Langfuse prompt object - use get_langchain_prompt with parameters
                prompt_template = prompt_rag.get_langchain_prompt(
                    chat_history=formatted_history,
                    question=query,
                    context=context_str
                )
                return prompt_template
            elif hasattr(prompt_rag, 'prompt'):
                # Direct prompt content - format with variables
                prompt_template = prompt_rag.prompt
                variables = {
                    "query": query,
                    "question": query,
                    "context": context_str,
                    "chat_history": formatted_history,
                }
                formatted_prompt = prompt_template
                for key, value in variables.items():
                    formatted_prompt = formatted_prompt.replace(f"{{{key}}}", str(value))
                return formatted_prompt
            elif isinstance(prompt_rag, str):
                # String prompt
                prompt_template = prompt_rag
                variables = {
                    "query": query,
                    "question": query,
                    "context": context_str,
                    "chat_history": formatted_history,
                }
                formatted_prompt = prompt_template
                for key, value in variables.items():
                    formatted_prompt = formatted_prompt.replace(f"{{{key}}}", str(value))
                return formatted_prompt
            else:
                raise PromptLoadError(
                    f"Unable to extract prompt content from Langfuse {prompt_name} object. "
                    "Please check the prompt format in Langfuse Dashboard."
                )
        except PromptLoadError:
            raise
        except Exception as e:
            raise PromptLoadError(
                f"Failed to format {prompt_name} prompt from Langfuse: {str(e)}"
            )
        parts = []

        # Add system prompt
        parts.append(self.system_prompt)
        parts.append("")

        # Add context
        if context.has_documents():
            if self.include_context_header:
                parts.append("=== RETRIEVED CONTEXT ===")
            parts.append(context.format_for_llm())
            parts.append("")

        # Add chat history
        if chat_history:
            history_text = self._format_chat_history(chat_history)
            if history_text:
                if self.include_history_header:
                    parts.append("=== CONVERSATION HISTORY ===")
                parts.append(history_text)
                parts.append("")

        # Add current query
        parts.append("=== CURRENT QUESTION ===")
        parts.append(query)

        return "\n".join(parts)

    def build_chat_prompt(
        self,
        query: str,
        chat_history: Optional[List[Message]] = None,
        system_instructions: Optional[str] = None
    ) -> str:
        """
        Build chat prompt without RAG context

        Args:
            query: User query
            chat_history: Chat history
            system_instructions: Optional system instructions

        Returns:
            Formatted prompt string
        """
        parts = []

        # Add system instructions
        if system_instructions:
            parts.append(system_instructions)
        else:
            parts.append(self.system_prompt)
        parts.append("")

        # Add chat history
        if chat_history:
            history_text = self._format_chat_history(chat_history)
            if history_text:
                if self.include_history_header:
                    parts.append("=== CONVERSATION HISTORY ===")
                parts.append(history_text)
                parts.append("")

        # Add current query
        parts.append("=== CURRENT QUESTION ===")
        parts.append(query)

        return "\n".join(parts)

    def build_tool_prompt(
        self,
        query: str,
        available_tools: List[str],
        chat_history: Optional[List[Message]] = None
    ) -> str:
        """
        Build prompt for tool selection

        Args:
            query: User query
            available_tools: List of available tool names
            chat_history: Chat history

        Returns:
            Formatted prompt string
        """
        parts = []

        parts.append("You are an AI assistant with access to the following tools:")
        parts.append("")
        for tool in available_tools:
            parts.append(f"- {tool}")
        parts.append("")
        parts.append("Analyze the user's question and determine which tools to use.")
        parts.append("")

        # Add chat history if available
        if chat_history:
            history_text = self._format_chat_history(chat_history)
            if history_text:
                parts.append("=== CONVERSATION HISTORY ===")
                parts.append(history_text)
                parts.append("")

        # Add current query
        parts.append("=== USER QUESTION ===")
        parts.append(query)

        return "\n".join(parts)

    def build_summarization_prompt(
        self,
        messages: List[Message],
        max_length: Optional[int] = None
    ) -> str:
        """
        Build prompt for conversation summarization

        Args:
            messages: Messages to summarize
            max_length: Optional maximum summary length

        Returns:
            Formatted prompt string
        """
        parts = []

        parts.append("Please summarize the following conversation concisely.")
        if max_length:
            parts.append(f"Keep the summary under {max_length} words.")
        parts.append("Focus on key points and important information.")
        parts.append("")
        parts.append("=== CONVERSATION TO SUMMARIZE ===")

        for msg in messages:
            role = msg.role.value.capitalize()
            parts.append(f"{role}: {msg.content}")

        parts.append("")
        parts.append("=== SUMMARY ===")

        return "\n".join(parts)

    def build_rewrite_query_prompt(
        self,
        query: str,
        chat_history: Optional[List[Message]] = None
    ) -> str:
        """
        Build prompt for query rewriting

        Args:
            query: Original query
            chat_history: Chat history for context

        Returns:
            Formatted prompt string
        """
        parts = []

        parts.append("Rewrite the following query to be more clear and specific.")
        parts.append("Consider the conversation history to resolve ambiguities.")
        parts.append("")

        if chat_history:
            history_text = self._format_chat_history(chat_history)
            if history_text:
                parts.append("=== CONVERSATION HISTORY ===")
                parts.append(history_text)
                parts.append("")

        parts.append("=== ORIGINAL QUERY ===")
        parts.append(query)
        parts.append("")
        parts.append("=== REWRITTEN QUERY ===")

        return "\n".join(parts)

    def _format_chat_history(self, messages: List[Message]) -> str:
        """
        Format chat history for prompt

        Args:
            messages: List of messages

        Returns:
            Formatted history string
        """
        if not messages:
            return ""

        # Limit to recent messages
        recent_messages = messages[-self.max_history_messages:]

        lines = []
        for msg in recent_messages:
            role = msg.role.value.capitalize()
            content = msg.content
            lines.append(f"{role}: {content}")

        return "\n".join(lines)

    def _build_from_template(
        self,
        template: PromptTemplate,
        query: str,
        context: RAGContext,
        chat_history: Optional[List[Message]] = None
    ) -> str:
        """
        Build prompt from template

        Args:
            template: Prompt template
            query: User query
            context: RAG context
            chat_history: Chat history

        Returns:
            Formatted prompt string
        """
        variables = {
            "query": query,
            "question": query,
            "context": context.format_for_llm() if context.has_documents() else "",
            "chat_history": self._format_chat_history(chat_history) if chat_history else "",
            "system_prompt": self.system_prompt
        }

        return template.format(**variables)

    def format_documents_for_context(
        self,
        documents: List[Document],
        include_scores: bool = True,
        include_metadata: bool = True
    ) -> str:
        """
        Format documents for context

        Args:
            documents: List of documents
            include_scores: Include relevance scores
            include_metadata: Include metadata

        Returns:
            Formatted documents string
        """
        if not documents:
            return ""

        parts = []
        for idx, doc in enumerate(documents, 1):
            doc_parts = [f"[Document {idx}]"]

            if include_metadata and doc.metadata:
                meta_str = ", ".join(f"{k}={v}" for k, v in doc.metadata.items() if v)
                if meta_str:
                    doc_parts.append(f"Metadata: {meta_str}")

            if include_scores:
                score = doc.hybrid_score or doc.relevance_score or doc.vector_score
                if score is not None:
                    doc_parts.append(f"Relevance: {score:.3f}")

            if doc.source:
                doc_parts.append(f"Source: {doc.source}")

            doc_parts.append("")
            doc_parts.append(doc.content)

            parts.append("\n".join(doc_parts))

        return "\n\n".join(parts)

    def calculate_prompt_length(self, prompt: str) -> Dict[str, int]:
        """
        Calculate prompt statistics

        Args:
            prompt: Prompt string

        Returns:
            Dictionary with statistics
        """
        return {
            "characters": len(prompt),
            "words": len(prompt.split()),
            "lines": len(prompt.split("\n")),
            "estimated_tokens": len(prompt) // 4  # Rough estimate
        }

