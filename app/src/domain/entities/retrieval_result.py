"""
Retrieval Result Entity
Represents the complete result of a RAG retrieval operation
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from uuid import uuid4
from enum import Enum

if TYPE_CHECKING:
    from .document import Document


class RetrievalStrategy(str, Enum):
    """Retrieval strategy enumeration"""
    VECTOR = "vector"
    KEYWORD = "keyword"
    HYBRID = "hybrid"
    SEMANTIC = "semantic"
    BM25 = "bm25"


@dataclass
class RetrievalResult:
    """
    Retrieval result entity - Aggregate Root

    Represents the complete result of a retrieval operation.
    Contains retrieved documents, metadata, and performance metrics.
    """

    query: str
    documents: List['Document']
    result_id: str = field(default_factory=lambda: str(uuid4()))
    strategy: RetrievalStrategy = RetrievalStrategy.HYBRID
    total_retrieved: int = 0
    retrieval_time_ms: Optional[int] = None
    reranked: bool = False
    filters_applied: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Post-initialization validation"""
        if not self.total_retrieved:
            self.total_retrieved = len(self.documents)

    def has_results(self) -> bool:
        """
        Check if retrieval returned any results

        Returns:
            True if has documents
        """
        return len(self.documents) > 0

    def get_top_k(self, k: int = 5) -> List['Document']:
        """
        Get top K documents by score

        Args:
            k: Number of documents to return

        Returns:
            Top K documents
        """
        return self.documents[:k]

    def get_average_score(self) -> Optional[float]:
        """
        Calculate average relevance score

        Returns:
            Average score or None
        """
        scores = []
        for doc in self.documents:
            score = doc.hybrid_score or doc.relevance_score or doc.vector_score
            if score is not None:
                scores.append(score)

        if not scores:
            return None

        return sum(scores) / len(scores)

    def get_min_score(self) -> Optional[float]:
        """
        Get minimum relevance score

        Returns:
            Minimum score or None
        """
        scores = [
            doc.hybrid_score or doc.relevance_score or doc.vector_score
            for doc in self.documents
            if doc.hybrid_score or doc.relevance_score or doc.vector_score
        ]
        return min(scores) if scores else None

    def get_max_score(self) -> Optional[float]:
        """
        Get maximum relevance score

        Returns:
            Maximum score or None
        """
        scores = [
            doc.hybrid_score or doc.relevance_score or doc.vector_score
            for doc in self.documents
            if doc.hybrid_score or doc.relevance_score or doc.vector_score
        ]
        return max(scores) if scores else None

    def filter_by_threshold(self, threshold: float = 0.7) -> List['Document']:
        """
        Filter documents by relevance threshold

        Args:
            threshold: Minimum relevance score

        Returns:
            Filtered documents
        """
        return [
            doc for doc in self.documents
            if doc.has_high_relevance(threshold)
        ]

    def get_unique_sources(self) -> List[str]:
        """
        Get list of unique document sources

        Returns:
            List of unique sources
        """
        sources = set()
        for doc in self.documents:
            if doc.source:
                sources.add(doc.source)
        return list(sources)

    def get_document_ids(self) -> List[str]:
        """
        Get list of all document IDs

        Returns:
            List of document IDs
        """
        return [doc.document_id for doc in self.documents]

    def add_metadata(self, key: str, value: Any) -> None:
        """
        Add metadata to result

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value

    def calculate_performance_metrics(self) -> Dict[str, Any]:
        """
        Calculate comprehensive performance metrics

        Returns:
            Dictionary with metrics
        """
        return {
            "total_documents": self.total_retrieved,
            "returned_documents": len(self.documents),
            "retrieval_time_ms": self.retrieval_time_ms,
            "average_score": self.get_average_score(),
            "min_score": self.get_min_score(),
            "max_score": self.get_max_score(),
            "unique_sources": len(self.get_unique_sources()),
            "strategy": self.strategy.value,
            "reranked": self.reranked,
            "filters_applied": bool(self.filters_applied)
        }

    def is_high_quality(
        self,
        min_docs: int = 3,
        min_avg_score: float = 0.6
    ) -> bool:
        """
        Check if retrieval result is high quality

        Args:
            min_docs: Minimum number of documents
            min_avg_score: Minimum average score

        Returns:
            True if high quality
        """
        if len(self.documents) < min_docs:
            return False

        avg_score = self.get_average_score()
        if avg_score is None or avg_score < min_avg_score:
            return False

        return True

    def __repr__(self) -> str:
        return (
            f"RetrievalResult("
            f"id={self.result_id[:8]}, "
            f"query='{self.query[:30]}...', "
            f"docs={len(self.documents)}, "
            f"strategy={self.strategy.value}, "
            f"avg_score={self.get_average_score():.3f if self.get_average_score() else 'N/A'}"
            f")"
        )

