"""
Document Controller
Handles document management requests
"""
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List

from app.src.application.use_cases.search_use_case import SearchUseCase
from app.src.application.dto.document_dto import (
    DocumentUploadRequestDTO,
    DocumentUploadResponseDTO,
)
from app.src.application.dto.search_dto import SearchRequestDTO, SearchResponseDTO


class DocumentController:
    """
    Document Controller

    Handles document upload, search, and management
    """

    def __init__(self, document_use_case: SearchUseCase, search_use_case: SearchUseCase):
        """
        Initialize document controller

        Args:
            document_use_case: Document use case (SearchUseCase for now)
            search_use_case: Search use case for search operations
        """
        self.document_use_case = document_use_case
        self.search_use_case = search_use_case

    async def upload_document(
        self,
        request: DocumentUploadRequestDTO
    ) -> DocumentUploadResponseDTO:
        """
        Handle document upload

        Args:
            request: Document upload request DTO

        Returns:
            Document upload response DTO
        """
        try:
            # Generate document ID
            document_id = str(uuid.uuid4())

            # Execute upload use case
            result = await self.document_use_case.upload_document(
                document_id=document_id,
                title=request.title,
                content=request.content,
                source=request.source,
                metadata={
                    **(request.metadata or {}),
                    "category": request.category,
                    "tags": request.tags,
                    "uploaded_by": request.uploaded_by,
                    "uploaded_at": datetime.now().isoformat(),
                }
            )

            # Build response
            return DocumentUploadResponseDTO(
                document_id=document_id,
                title=request.title,
                status="success",
                message="Document uploaded and processed successfully",
                chunks_created=result.get("chunks_created"),
                embeddings_generated=result.get("embeddings_generated"),
                timestamp=datetime.now(),
            )

        except Exception as e:
            return DocumentUploadResponseDTO(
                document_id=document_id if 'document_id' in locals() else "unknown",
                title=request.title,
                status="failed",
                message=f"Document upload failed: {str(e)}",
                timestamp=datetime.now(),
            )

    async def search_documents(
        self,
        request: SearchRequestDTO
    ) -> SearchResponseDTO:
        """
        Handle document search

        Args:
            request: Search request DTO

        Returns:
            Search response DTO
        """
        start_time = time.time()

        try:
            # Execute search use case
            search_response = await self.search_use_case.search_documents(request)

            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            if not search_response.latency_ms:
                search_response.latency_ms = latency_ms

            return search_response

        except Exception as e:
            raise RuntimeError(f"Search failed: {str(e)}")

    async def get_document(self, document_id: str) -> dict:
        """
        Get document by ID

        Args:
            document_id: Document ID

        Returns:
            Document details
        """
        return await self.document_use_case.get_document(document_id)

    async def delete_document(self, document_id: str) -> bool:
        """
        Delete document

        Args:
            document_id: Document ID

        Returns:
            True if successful
        """
        return await self.document_use_case.delete_document(document_id)

    async def list_documents(
        self,
        skip: int = 0,
        limit: int = 50
    ) -> list:
        """
        List all documents

        Args:
            skip: Number of documents to skip
            limit: Maximum number of documents to return

        Returns:
            List of documents
        """
        return await self.document_use_case.list_documents(skip, limit)
