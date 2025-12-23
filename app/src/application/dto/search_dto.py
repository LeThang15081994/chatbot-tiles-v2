"""
Search-related Data Transfer Objects
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class CollectionType(str, Enum):
    """Collection type enum"""
    COMPANY_DOCUMENT = "company_document"
    PRODUCTS = "products"
    PRODUCTS_INFO = "products_info"  # Collection for company info search
    COLLECTION_INFO = "collection_info"  # Collection for collection info search
    AUTO = "auto"  # Auto-detect based on query


class SearchRequestDTO(BaseModel):
    """Search request DTO"""
    query: str = Field(
        ...,
        description="Search query string for vector and BM25 hybrid search",
        min_length=1
    )
    top_k: int = Field(
        default=10,
        description="Number of results to return",
        ge=1,
        le=50
    )
    search_type: str = Field(
        default="hybrid",
        description="Search type: similarity, bm25, hybrid"
    )
    similarity_threshold: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Similarity threshold"
    )
    with_score: bool = Field(
        default=False,
        description="Whether to return similarity scores"
    )
    collection_name: Optional[CollectionType] = Field(
        default=None,
        description="Collection to search in: company_document, products, or auto-detect"
    )
    metadata_filter: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Filter by metadata fields"
    )
    category: Optional[str] = Field(
        default=None,
        description="Document category filter"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Document tags filter"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "What is wooden tile?",
                "top_k": 5,
                "with_score": True,
                "collection_name": "products",
                "metadata_filter": {"brandName": "Atlas Concorde"}
            }
        }


class SearchMetadataDTO(BaseModel):
    """Search result metadata DTO"""
    id: Optional[str] = Field(default=None, description="Document ID")
    category: Optional[str] = Field(default=None, description="Document category")
    source: Optional[str] = Field(default=None, description="Source name")
    brand_name: Optional[str] = Field(default=None, description="Brand name")
    collection_name: Optional[str] = Field(default=None, description="Collection name")
    updated_time: Optional[str] = Field(default=None, description="Last update time")
    hybrid_score: Optional[float] = Field(default=None, description="Hybrid search score")
    vector_score: Optional[float] = Field(default=None, description="Vector similarity score")
    bm25_score: Optional[float] = Field(default=None, description="BM25 score")


class SearchResultDTO(BaseModel):
    """Single search result DTO"""
    content: str = Field(..., description="Document content")
    metadata: SearchMetadataDTO = Field(..., description="Result metadata")
    score: Optional[float] = Field(default=None, description="Relevance score")


class SearchResponseDTO(BaseModel):
    """Search response DTO"""
    results: List[SearchResultDTO] = Field(..., description="Search results")
    query: str = Field(..., description="Original query")
    collection_name: str = Field(..., description="Collection searched")
    total_results: int = Field(..., description="Total number of results")
    search_type: str = Field(..., description="Search type used")
    latency_ms: Optional[float] = Field(default=None, description="Search latency in ms")
    processing_time_ms: Optional[int] = Field(default=None, description="Processing time in ms")

    class Config:
        json_schema_extra = {
            "example": {
                "results": [
                    {
                        "content": "Gạch wooden là loại gạch...",
                        "metadata": {
                            "category": "products",
                            "brand_name": "Atlas Concorde",
                            "hybrid_score": 0.95
                        },
                        "score": 0.95
                    }
                ],
                "query": "wooden tile",
                "collection_name": "products",
                "total_results": 5,
                "processing_time_ms": 250
            }
        }


# Tool Search Arguments DTOs
# These DTOs are used as args_schema for LangChain StructuredTool

class CompanyInfoSearchArgsDTO(BaseModel):
    """Arguments DTO for search_company_info tool"""
    query: str = Field(..., description="Search query about company information")
    top_k: int = Field(5, ge=1, le=20, description="Number of documents to retrieve (1-20)")


class CollectionInfoSearchArgsDTO(BaseModel):
    """Arguments DTO for search_collection_info tool"""
    query: str = Field(..., description="Search query about tile collections")
    top_k: int = Field(5, ge=1, le=20, description="Number of documents to retrieve (1-20)")


class ProductsSearchArgsDTO(BaseModel):
    """Arguments DTO for search_products tool"""
    query: str = Field(..., description="Search query about specific products")
    top_k: int = Field(5, ge=1, le=20, description="Number of documents to retrieve (1-20)")


class AddToCartArgsDTO(BaseModel):
    """Arguments DTO for add_to_cart tool"""
    product_code: str = Field(..., description="Product code to add to cart")
    quantity: int = Field(1, ge=1, le=100, description="Quantity to add (1-100)")
    session_id: Optional[str] = Field(default=None, description="Session ID for cart management")