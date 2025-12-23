"""
Document-related Data Transfer Objects
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class DocumentMetadataDTO(BaseModel):
    """Document metadata DTO"""
    id: Optional[str] = Field(default=None, description="Document ID")
    source: Optional[str] = Field(default=None, description="Source name")
    category: Optional[str] = Field(default=None, description="Document category")
    brand_name: Optional[str] = Field(default=None, description="Brand name")
    created_at: Optional[str] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[str] = Field(default=None, description="Last update timestamp")
    custom_fields: Optional[Dict[str, Any]] = Field(default=None, description="Custom metadata fields")


class DocumentDTO(BaseModel):
    """Document DTO"""
    id: str = Field(..., description="Unique document ID")
    content: str = Field(..., description="Document content")
    metadata: DocumentMetadataDTO = Field(..., description="Document metadata")
    vector: Optional[List[float]] = Field(default=None, description="Embedding vector (if included)")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "doc_12345",
                "content": "Gạch wooden là loại gạch lát sàn cao cấp...",
                "metadata": {
                    "source": "product_catalog",
                    "category": "flooring_tiles",
                    "brand_name": "Atlas Concorde"
                }
            }
        }


class DocumentUploadRequestDTO(BaseModel):
    """Document upload request DTO"""
    title: str = Field(..., min_length=1, description="Document title")
    content: str = Field(..., min_length=1, description="Document content")
    source: str = Field(..., description="Document source")

    # Metadata
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    category: Optional[str] = Field(default=None, description="Document category")
    tags: Optional[List[str]] = Field(default=None, description="Document tags")

    # User info
    uploaded_by: str = Field(..., description="User who uploaded")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Ceramic Tile Installation Guide",
                "content": "Step by step guide for installing ceramic tiles...",
                "source": "internal_docs",
                "category": "installation",
                "tags": ["ceramic", "installation", "guide"],
                "uploaded_by": "admin"
            }
        }


class DocumentUploadResponseDTO(BaseModel):
    """Document upload response DTO"""
    document_id: str = Field(..., description="Uploaded document ID")
    title: str = Field(..., description="Document title")
    status: str = Field(..., description="Upload status")
    message: str = Field(..., description="Status message")

    # Processing info
    chunks_created: Optional[int] = Field(default=None, description="Number of chunks created")
    embeddings_generated: Optional[int] = Field(default=None, description="Number of embeddings")

    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc123",
                "title": "Ceramic Tile Installation Guide",
                "status": "success",
                "message": "Document uploaded and processed successfully",
                "chunks_created": 25,
                "embeddings_generated": 25
            }
        }


class DocumentCreateRequestDTO(BaseModel):
    """Request DTO for creating a document"""
    content: str = Field(..., description="Document content", min_length=1)
    metadata: Optional[DocumentMetadataDTO] = Field(default=None, description="Document metadata")
    collection_name: str = Field(default="company_document", description="Target collection")


class DocumentUpdateRequestDTO(BaseModel):
    """Request DTO for updating a document"""
    id: str = Field(..., description="Document ID to update")
    content: Optional[str] = Field(default=None, description="Updated content")
    metadata: Optional[DocumentMetadataDTO] = Field(default=None, description="Updated metadata")
    collection_name: str = Field(default="company_document", description="Target collection")


class DocumentDeleteRequestDTO(BaseModel):
    """Request DTO for deleting document(s)"""
    ids: List[str] = Field(..., description="List of document IDs to delete", min_items=1)
    collection_name: str = Field(default="company_document", description="Target collection")


class DocumentOperationResponseDTO(BaseModel):
    """Response DTO for document operations"""
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Operation result message")
    affected_count: int = Field(..., description="Number of documents affected")
    document_ids: Optional[List[str]] = Field(default=None, description="IDs of affected documents")
