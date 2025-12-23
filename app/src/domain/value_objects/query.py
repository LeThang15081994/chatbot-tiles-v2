"""
Search Query Value Object
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass(frozen=True)
class SearchQuery:
    """
    Search query value object

    Represents a search query with parameters.
    Immutable to ensure query integrity.
    """

    text: str
    top_k: int = 5
    collection_name: Optional[str] = None
    metadata_filter: Optional[Dict[str, Any]] = None
    search_type: str = "hybrid"  # hybrid, vector, bm25

    def __post_init__(self):
        """Validate search query"""
        if not self.text or not isinstance(self.text, str):
            raise ValueError("Query text must be a non-empty string")

        if self.top_k < 1 or self.top_k > 100:
            raise ValueError("top_k must be between 1 and 100")

        if self.search_type not in ["hybrid", "vector", "bm25"]:
            raise ValueError("search_type must be hybrid, vector, or bm25")

    def is_product_query(self) -> bool:
        """
        Check if this is likely a product query

        Returns:
            True if product-related
        """
        product_keywords = ['gạch', 'tile', 'product', 'price', 'wooden', 'ceramic']
        text_lower = self.text.lower()
        return any(keyword in text_lower for keyword in product_keywords)

    def get_suggested_collection(self) -> str:
        """
        Get suggested collection based on query

        Returns:
            Suggested collection name
        """
        if self.collection_name:
            return self.collection_name

        return "products" if self.is_product_query() else "company_document"

    def truncate_text(self, max_length: int = 100) -> str:
        """
        Get truncated query text

        Args:
            max_length: Maximum length

        Returns:
            Truncated text
        """
        if len(self.text) <= max_length:
            return self.text
        return self.text[:max_length] + "..."

    def __str__(self) -> str:
        return f"{self.text} (top_k={self.top_k}, type={self.search_type})"

    def __repr__(self) -> str:
        return f"SearchQuery(text='{self.truncate_text(50)}', top_k={self.top_k})"

