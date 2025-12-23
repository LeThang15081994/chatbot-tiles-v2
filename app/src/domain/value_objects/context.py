"""
RAG Context Value Object
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class RAGContext:
    """
    RAG context value object

    Represents the retrieved context for RAG generation.
    Immutable to ensure context integrity.
    """

    documents: tuple  # Tuple of Document entities (immutable)
    query: str
    total_documents: int
    context_text: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate RAG context"""
        if not isinstance(self.documents, tuple):
            # Convert to tuple if list provided
            object.__setattr__(self, 'documents', tuple(self.documents))

        if self.total_documents < 0:
            raise ValueError("total_documents must be non-negative")

    @classmethod
    def from_documents(
        cls,
        documents: List,
        query: str,
        context_text: Optional[str] = None
    ) -> 'RAGContext':
        """
        Create RAGContext from document list

        Args:
            documents: List of Document entities
            query: Original query
            context_text: Pre-formatted context text

        Returns:
            RAGContext instance
        """
        return cls(
            documents=tuple(documents),
            query=query,
            total_documents=len(documents),
            context_text=context_text
        )

    def has_documents(self) -> bool:
        """
        Check if context has any documents

        Returns:
            True if has documents
        """
        return self.total_documents > 0

    def get_document_ids(self) -> List[str]:
        """
        Get list of document IDs

        Returns:
            List of document IDs
        """
        return [doc.document_id for doc in self.documents]

    def get_sources(self) -> List[str]:
        """
        Get unique sources from documents

        Returns:
            List of unique sources
        """
        sources = set()
        for doc in self.documents:
            if doc.source:
                sources.add(doc.source)
        return list(sources)

    def format_for_llm(self, max_length: Optional[int] = None) -> str:
        """
        Format context for LLM consumption

        Args:
            max_length: Optional maximum length

        Returns:
            Formatted context string
        """
        if self.context_text:
            text = self.context_text
        else:
            parts = []
            for idx, doc in enumerate(self.documents, 1):
                parts.append(f"[Document {idx}]\n{doc.content}")
            text = "\n\n".join(parts)

        if max_length and len(text) > max_length:
            return text[:max_length] + "\n... [truncated]"

        return text

    def get_average_score(self) -> Optional[float]:
        """
        Get average relevance score across documents

        Returns:
            Average score or None
        """
        scores = [
            doc.hybrid_score or doc.relevance_score or doc.vector_score
            for doc in self.documents
            if doc.hybrid_score or doc.relevance_score or doc.vector_score
        ]

        if not scores:
            return None

        return sum(scores) / len(scores)

    def __repr__(self) -> str:
        return f"RAGContext(documents={self.total_documents}, query='{self.query[:50]}...')"

