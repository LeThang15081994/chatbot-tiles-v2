"""
Retrieval Configuration Value Object
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass(frozen=True)
class RetrievalConfig:
    """
    Retrieval configuration value object

    Represents configuration for RAG retrieval operations.
    Immutable to ensure configuration consistency.
    """

    top_k: int = 5
    score_threshold: float = 0.0
    rerank: bool = False
    rerank_top_k: Optional[int] = None
    hybrid_alpha: float = 0.5  # 0.0 = pure keyword, 1.0 = pure vector
    include_metadata: bool = True
    max_context_length: int = 4000
    filters: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate retrieval configuration"""
        if self.top_k < 1 or self.top_k > 100:
            raise ValueError("top_k must be between 1 and 100")

        if not 0.0 <= self.score_threshold <= 1.0:
            raise ValueError("score_threshold must be between 0.0 and 1.0")

        if not 0.0 <= self.hybrid_alpha <= 1.0:
            raise ValueError("hybrid_alpha must be between 0.0 and 1.0")

        if self.rerank and self.rerank_top_k:
            if self.rerank_top_k < self.top_k:
                raise ValueError("rerank_top_k must be >= top_k")

        if self.max_context_length < 100:
            raise ValueError("max_context_length must be at least 100")

    @classmethod
    def default(cls) -> 'RetrievalConfig':
        """
        Create default configuration

        Returns:
            Default RetrievalConfig
        """
        return cls()

    @classmethod
    def for_high_precision(cls) -> 'RetrievalConfig':
        """
        Create configuration optimized for high precision

        Returns:
            High precision RetrievalConfig
        """
        return cls(
            top_k=3,
            score_threshold=0.7,
            rerank=True,
            rerank_top_k=10,
            hybrid_alpha=0.7
        )

    @classmethod
    def for_high_recall(cls) -> 'RetrievalConfig':
        """
        Create configuration optimized for high recall

        Returns:
            High recall RetrievalConfig
        """
        return cls(
            top_k=10,
            score_threshold=0.3,
            rerank=False,
            hybrid_alpha=0.5
        )

    @classmethod
    def for_semantic_search(cls) -> 'RetrievalConfig':
        """
        Create configuration for pure semantic search

        Returns:
            Semantic search RetrievalConfig
        """
        return cls(
            top_k=5,
            score_threshold=0.5,
            hybrid_alpha=1.0,  # Pure vector
            rerank=True
        )

    @classmethod
    def for_keyword_search(cls) -> 'RetrievalConfig':
        """
        Create configuration for keyword search

        Returns:
            Keyword search RetrievalConfig
        """
        return cls(
            top_k=5,
            score_threshold=0.0,
            hybrid_alpha=0.0,  # Pure keyword
            rerank=False
        )

    def is_pure_vector(self) -> bool:
        """Check if this is pure vector search"""
        return self.hybrid_alpha == 1.0

    def is_pure_keyword(self) -> bool:
        """Check if this is pure keyword search"""
        return self.hybrid_alpha == 0.0

    def is_hybrid(self) -> bool:
        """Check if this is hybrid search"""
        return 0.0 < self.hybrid_alpha < 1.0

    def should_rerank(self) -> bool:
        """Check if reranking is enabled"""
        return self.rerank

    def get_effective_rerank_k(self) -> int:
        """
        Get effective rerank top_k value

        Returns:
            Rerank top_k or default
        """
        if not self.rerank:
            return self.top_k
        return self.rerank_top_k or (self.top_k * 3)

    def with_filters(self, filters: Dict[str, Any]) -> 'RetrievalConfig':
        """
        Create new config with filters

        Args:
            filters: Metadata filters

        Returns:
            New RetrievalConfig with filters
        """
        return RetrievalConfig(
            top_k=self.top_k,
            score_threshold=self.score_threshold,
            rerank=self.rerank,
            rerank_top_k=self.rerank_top_k,
            hybrid_alpha=self.hybrid_alpha,
            include_metadata=self.include_metadata,
            max_context_length=self.max_context_length,
            filters=filters
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary

        Returns:
            Dictionary representation
        """
        return {
            "top_k": self.top_k,
            "score_threshold": self.score_threshold,
            "rerank": self.rerank,
            "rerank_top_k": self.rerank_top_k,
            "hybrid_alpha": self.hybrid_alpha,
            "include_metadata": self.include_metadata,
            "max_context_length": self.max_context_length,
            "filters": self.filters
        }

    def __repr__(self) -> str:
        return (
            f"RetrievalConfig("
            f"top_k={self.top_k}, "
            f"threshold={self.score_threshold}, "
            f"hybrid_alpha={self.hybrid_alpha}, "
            f"rerank={self.rerank}"
            f")"
        )

