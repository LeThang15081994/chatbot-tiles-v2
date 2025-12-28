"""
Document Router
Handles document management endpoints
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from dependency_injector.wiring import inject, Provide

from app.src.presentation.controllers.document_controller import DocumentController
from app.src.application.dto.document_dto import (
    DocumentUploadRequestDTO,
    DocumentUploadResponseDTO,
)
from app.src.application.dto.search_dto import SearchRequestDTO, SearchResponseDTO
from app.src.bootstrap.container import Container


router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentUploadResponseDTO)
@inject
async def upload_document(
    request: DocumentUploadRequestDTO,
    controller: DocumentController = Depends(Provide[Container.document_controller]),
) -> DocumentUploadResponseDTO:
    """Upload a document"""
    try:
        response = await controller.upload_document(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload/file", response_model=DocumentUploadResponseDTO)
@inject
async def upload_document_file(
    file: UploadFile = File(...),
    title: str = Form(...),
    source: str = Form(...),
    category: Optional[str] = Form(None),
    uploaded_by: str = Form(...),
    controller: DocumentController = Depends(Provide[Container.document_controller]),
) -> DocumentUploadResponseDTO:
    """Upload a document from file"""
    try:
        # Read file content
        content = await file.read()
        content_text = content.decode("utf-8")

        # Create DTO
        upload_dto = DocumentUploadRequestDTO(
            title=title,
            content=content_text,
            source=source,
            category=category,
            uploaded_by=uploaded_by,
            metadata={
                "filename": file.filename,
                "content_type": file.content_type,
            }
        )

        response = await controller.upload_document(upload_dto)
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=SearchResponseDTO)
@inject
async def search_documents(
    request: SearchRequestDTO,
    controller: DocumentController = Depends(Provide[Container.document_controller]),
) -> SearchResponseDTO:
    """Search documents"""
    try:
        response = await controller.search_documents(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}")
@inject
async def get_document(
    document_id: str,
    controller: DocumentController = Depends(Provide[Container.document_controller]),
):
    """Get document by ID"""
    try:
        document = await controller.get_document(document_id)
        if document is None:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}")
@inject
async def delete_document(
    document_id: str,
    controller: DocumentController = Depends(Provide[Container.document_controller]),
):
    """Delete document"""
    try:
        success = await controller.delete_document(document_id)
        if success:
            return {"message": f"Document {document_id} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
@inject
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    controller: DocumentController = Depends(Provide[Container.document_controller]),
):
    """List all documents"""
    try:
        documents = await controller.list_documents(skip, limit)
        return {
            "documents": documents,
            "skip": skip,
            "limit": limit,
            "total": len(documents),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
