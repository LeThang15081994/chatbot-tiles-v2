"""
Document Entity
Represents a retrieved document in RAG
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import uuid4


@dataclass
class Document:
    """
    Document entity

    Represents a document retrieved from vector store.
    Contains content, metadata, and relevance scoring.
    """

    content: str
    document_id: str = field(default_factory=lambda: str(uuid4()))
    source: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    relevance_score: Optional[float] = None
    vector_score: Optional[float] = None
    bm25_score: Optional[float] = None
    hybrid_score: Optional[float] = None
    retrieved_at: datetime = field(default_factory=datetime.now)

    def get_score(self, score_type: str = "hybrid") -> Optional[float]:
        """
        Get relevance score by type

        Args:
            score_type: Type of score (hybrid, vector, bm25, relevance)

        Returns:
            Score value if available
        """
        score_map = {
            "hybrid": self.hybrid_score,
            "vector": self.vector_score,
            "bm25": self.bm25_score,
            "relevance": self.relevance_score
        }
        return score_map.get(score_type)

    def get_metadata_field(self, key: str, default: Any = None) -> Any:
        """
        Get metadata field value

        Args:
            key: Metadata key
            default: Default value if key not found

        Returns:
            Metadata value
        """
        return self.metadata.get(key, default)

    def has_high_relevance(self, threshold: float = 0.7) -> bool:
        """
        Check if document has high relevance

        Args:
            threshold: Relevance threshold

        Returns:
            True if highly relevant
        """
        score = self.hybrid_score or self.relevance_score or self.vector_score
        return score is not None and score >= threshold

    def truncate_content(self, max_length: int = 500) -> str:
        """
        Get truncated content

        Args:
            max_length: Maximum length

        Returns:
            Truncated content
        """
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length] + "..."

    def format_for_context(self, include_metadata: bool = True) -> str:
        """
        Format document for LLM context

        Args:
            include_metadata: Whether to include metadata

        Returns:
            Formatted document string
        """
        parts = [self.content]

        if include_metadata and self.metadata:
            meta_str = ", ".join(f"{k}={v}" for k, v in self.metadata.items() if v)
            if meta_str:
                parts.append(f"[Metadata: {meta_str}]")

        if self.hybrid_score:
            parts.append(f"[Relevance: {self.hybrid_score:.2f}]")

        return "\n".join(parts)

    def __repr__(self) -> str:
        content_preview = self.truncate_content(50)
        score = self.hybrid_score or self.relevance_score
        return f"Document(id={self.document_id[:8]}, score={score}, content='{content_preview}')"

