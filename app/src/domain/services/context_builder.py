"""
Context Builder Domain Service
Builds RAG context from retrieved documents
"""
from typing import List, Optional, Dict, Any
from app.src.domain.entities.document import Document
from app.src.domain.value_objects.context import RAGContext


class ContextBuilderService:
    """
    Context builder domain service

    Responsible for building LLM context from retrieved documents.
    Core RAG business logic.
    """

    def __init__(
        self,
        max_context_length: int = 4000,
        include_metadata: bool = True,
        include_scores: bool = True
    ):
        """
        Initialize context builder

        Args:
            max_context_length: Maximum context length in characters
            include_metadata: Whether to include document metadata
            include_scores: Whether to include relevance scores
        """
        self.max_context_length = max_context_length
        self.include_metadata = include_metadata
        self.include_scores = include_scores

    def build_context(
        self,
        documents: List[Document],
        query: str
    ) -> RAGContext:
        """
        Build RAG context from documents

        Args:
            documents: List of retrieved documents
            query: Original search query

        Returns:
            RAGContext value object
        """
        if not documents:
            return RAGContext.from_documents(
                documents=[],
                query=query,
                context_text=""
            )

        # Sort documents by relevance score
        sorted_docs = self._sort_by_relevance(documents)

        # Build context text
        context_text = self._format_documents(sorted_docs)

        return RAGContext.from_documents(
            documents=sorted_docs,
            query=query,
            context_text=context_text
        )

    def _sort_by_relevance(self, documents: List[Document]) -> List[Document]:
        """
        Sort documents by relevance score

        Args:
            documents: List of documents

        Returns:
            Sorted list
        """
        def get_score(doc: Document) -> float:
            return (
                doc.hybrid_score or
                doc.relevance_score or
                doc.vector_score or
                0.0
            )

        return sorted(documents, key=get_score, reverse=True)

    def _format_documents(self, documents: List[Document]) -> str:
        """
        Format documents into context string

        Args:
            documents: List of documents

        Returns:
            Formatted context string
        """
        parts = []
        current_length = 0

        for idx, doc in enumerate(documents, 1):
            # Format document
            doc_text = self._format_single_document(doc, idx)
            doc_length = len(doc_text)

            # Check if adding this document exceeds max length
            if current_length + doc_length > self.max_context_length:
                if idx == 1:
                    # At least include first document (truncated if needed)
                    remaining = self.max_context_length - current_length
                    parts.append(doc_text[:remaining] + "\n... [truncated]")
                break

            parts.append(doc_text)
            current_length += doc_length

        header = "--- Retrieved Documents ---\n\n"
        return header + "\n\n".join(parts)

    def _format_single_document(self, doc: Document, index: int) -> str:
        """
        Format a single document

        Args:
            doc: Document to format
            index: Document index

        Returns:
            Formatted document string
        """
        lines = [f"[Document {index}]"]

        # Add metadata if enabled
        if self.include_metadata and doc.metadata:
            meta_items = []
            for key, value in doc.metadata.items():
                if value:
                    meta_items.append(f"{key}={value}")
            if meta_items:
                lines.append(f"Metadata: {', '.join(meta_items)}")

        # Add score if enabled
        if self.include_scores:
            score = doc.hybrid_score or doc.relevance_score or doc.vector_score
            if score is not None:
                lines.append(f"Relevance Score: {score:.3f}")

        # Add source if available
        if doc.source:
            lines.append(f"Source: {doc.source}")

        # Add content
        lines.append("")
        lines.append(doc.content)

        return "\n".join(lines)

    def build_tool_message_context(self, tool_messages: List[str]) -> str:
        """
        Build context from tool messages

        Args:
            tool_messages: List of tool message contents

        Returns:
            Formatted context string
        """
        if not tool_messages:
            return ""

        separator = "\n\n--- Retrieved Documents ---\n\n"
        return separator.join(tool_messages)

    def calculate_context_stats(self, context: RAGContext) -> dict:
        """
        Calculate statistics for context

        Args:
            context: RAG context

        Returns:
            Dictionary with statistics
        """
        return {
            "total_documents": context.total_documents,
            "total_characters": len(context.context_text or ""),
            "average_score": context.get_average_score(),
            "unique_sources": len(context.get_sources()),
            "has_high_relevance": any(
                doc.has_high_relevance() for doc in context.documents
            )
        }

    def format_tool_results(
        self,
        search_results: List[Dict[str, Any]],
        max_content_length: int = 500
    ) -> str:
        """
        Format search results for LLM tool message (JSON format)

        Args:
            search_results: List of search result dictionaries with:
                - content: str
                - score: float
                - metadata: dict
            max_content_length: Maximum content length per result

        Returns:
            JSON string formatted for LLM tool message
        """
        import json

        formatted_results = []
        for result in search_results:
            content = result.get("content", "")
            if len(content) > max_content_length:
                content = content[:max_content_length]

            formatted_results.append({
                "content": content,
                "score": result.get("score"),
                "metadata": result.get("metadata", {})
            })

        tool_result = {
            "total_results": len(formatted_results),
            "results": formatted_results
        }

        return json.dumps(tool_result, ensure_ascii=False)

