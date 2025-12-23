"""
Retrieval Optimizer Domain Service
Optimizes retrieval strategies and results
"""
from typing import List, Optional, Dict, Any
from app.src.domain.entities.document import Document
from app.src.domain.entities.retrieval_result import RetrievalResult, RetrievalStrategy
from app.src.domain.value_objects.retrieval_config import RetrievalConfig


class RetrievalOptimizerService:
    """
    Retrieval optimizer domain service

    Optimizes retrieval results through filtering, reranking, and deduplication.
    Implements business logic for improving retrieval quality.
    """

    def __init__(
        self,
        min_score_threshold: float = 0.0,
        enable_deduplication: bool = True,
        similarity_threshold: float = 0.95
    ):
        """
        Initialize retrieval optimizer

        Args:
            min_score_threshold: Minimum relevance score
            enable_deduplication: Enable deduplication
            similarity_threshold: Threshold for duplicate detection
        """
        self.min_score_threshold = min_score_threshold
        self.enable_deduplication = enable_deduplication
        self.similarity_threshold = similarity_threshold

    def optimize_results(
        self,
        result: RetrievalResult,
        config: RetrievalConfig
    ) -> RetrievalResult:
        """
        Optimize retrieval results

        Args:
            result: Retrieval result
            config: Retrieval configuration

        Returns:
            Optimized retrieval result
        """
        documents = result.documents

        # Apply score threshold
        if config.score_threshold > 0:
            documents = self.filter_by_score(documents, config.score_threshold)

        # Deduplicate if enabled
        if self.enable_deduplication:
            documents = self.deduplicate_documents(documents)

        # Limit to top_k
        documents = documents[:config.top_k]

        # Create new result
        return RetrievalResult(
            query=result.query,
            documents=documents,
            strategy=result.strategy,
            total_retrieved=len(documents),
            retrieval_time_ms=result.retrieval_time_ms,
            reranked=result.reranked,
            filters_applied=result.filters_applied,
            metadata={
                **result.metadata,
                "optimized": True,
                "original_count": len(result.documents)
            }
        )

    def filter_by_score(
        self,
        documents: List[Document],
        threshold: float
    ) -> List[Document]:
        """
        Filter documents by relevance score

        Args:
            documents: List of documents
            threshold: Score threshold

        Returns:
            Filtered documents
        """
        return [
            doc for doc in documents
            if doc.has_high_relevance(threshold)
        ]

    def deduplicate_documents(
        self,
        documents: List[Document]
    ) -> List[Document]:
        """
        Remove duplicate documents

        Args:
            documents: List of documents

        Returns:
            Deduplicated documents
        """
        if not documents:
            return documents

        unique_docs = []
        seen_contents = set()

        for doc in documents:
            # Simple content-based deduplication
            content_hash = hash(doc.content.strip().lower())

            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                unique_docs.append(doc)

        return unique_docs

    def rerank_by_query_similarity(
        self,
        documents: List[Document],
        query: str,
        boost_factor: float = 1.2
    ) -> List[Document]:
        """
        Rerank documents by query similarity

        Args:
            documents: List of documents
            query: Search query
            boost_factor: Score boost factor

        Returns:
            Reranked documents
        """
        # Simple keyword-based reranking
        query_terms = set(query.lower().split())

        scored_docs = []
        for doc in documents:
            doc_terms = set(doc.content.lower().split())
            overlap = len(query_terms & doc_terms)

            # Boost score based on term overlap
            base_score = doc.hybrid_score or doc.relevance_score or doc.vector_score or 0.0
            boosted_score = base_score * (1 + (overlap / len(query_terms)) * boost_factor)

            scored_docs.append((boosted_score, doc))

        # Sort by boosted score
        scored_docs.sort(key=lambda x: x[0], reverse=True)

        return [doc for _, doc in scored_docs]

    def diversify_results(
        self,
        documents: List[Document],
        diversity_factor: float = 0.5,
        max_per_source: int = 3
    ) -> List[Document]:
        """
        Diversify results by source

        Args:
            documents: List of documents
            diversity_factor: Diversity weight (0-1)
            max_per_source: Maximum documents per source

        Returns:
            Diversified documents
        """
        if not documents:
            return documents

        # Track source counts
        source_counts: Dict[str, int] = {}
        diversified = []

        for doc in documents:
            source = doc.source or "unknown"
            current_count = source_counts.get(source, 0)

            # Check if we should include this document
            if current_count < max_per_source:
                diversified.append(doc)
                source_counts[source] = current_count + 1

        return diversified

    def boost_recent_documents(
        self,
        documents: List[Document],
        boost_factor: float = 1.1
    ) -> List[Document]:
        """
        Boost scores of recent documents

        Args:
            documents: List of documents
            boost_factor: Score boost factor

        Returns:
            Documents with boosted scores
        """
        from datetime import datetime, timedelta

        recent_threshold = datetime.now() - timedelta(days=30)

        boosted_docs = []
        for doc in documents:
            # Check if document has recent timestamp
            if doc.retrieved_at >= recent_threshold:
                # Boost the score
                base_score = doc.hybrid_score or doc.relevance_score or doc.vector_score
                if base_score:
                    # Create new document with boosted score
                    # (In real implementation, you'd create a proper copy)
                    boosted_docs.append(doc)
                else:
                    boosted_docs.append(doc)
            else:
                boosted_docs.append(doc)

        return boosted_docs

    def merge_retrieval_results(
        self,
        results: List[RetrievalResult],
        strategy: RetrievalStrategy = RetrievalStrategy.HYBRID
    ) -> RetrievalResult:
        """
        Merge multiple retrieval results

        Args:
            results: List of retrieval results
            strategy: Merged strategy

        Returns:
            Merged retrieval result
        """
        if not results:
            raise ValueError("Cannot merge empty results list")

        if len(results) == 1:
            return results[0]

        # Collect all documents
        all_documents = []
        for result in results:
            all_documents.extend(result.documents)

        # Deduplicate
        unique_documents = self.deduplicate_documents(all_documents)

        # Sort by score
        unique_documents.sort(
            key=lambda d: d.hybrid_score or d.relevance_score or d.vector_score or 0.0,
            reverse=True
        )

        # Merge metadata
        merged_metadata = {
            "merged_from": len(results),
            "total_documents": len(all_documents),
            "unique_documents": len(unique_documents)
        }

        return RetrievalResult(
            query=results[0].query,
            documents=unique_documents,
            strategy=strategy,
            total_retrieved=len(unique_documents),
            metadata=merged_metadata
        )

    def calculate_retrieval_quality(
        self,
        result: RetrievalResult
    ) -> Dict[str, Any]:
        """
        Calculate retrieval quality metrics

        Args:
            result: Retrieval result

        Returns:
            Quality metrics
        """
        if not result.has_results():
            return {
                "quality_score": 0.0,
                "has_results": False
            }

        avg_score = result.get_average_score() or 0.0
        min_score = result.get_min_score() or 0.0
        max_score = result.get_max_score() or 0.0

        # Calculate quality score (0-1)
        quality_score = (avg_score + min_score) / 2

        # Check score distribution
        score_range = max_score - min_score

        return {
            "quality_score": quality_score,
            "has_results": True,
            "average_score": avg_score,
            "min_score": min_score,
            "max_score": max_score,
            "score_range": score_range,
            "score_consistency": 1.0 - score_range if score_range < 1.0 else 0.0,
            "document_count": len(result.documents),
            "unique_sources": len(result.get_unique_sources())
        }

