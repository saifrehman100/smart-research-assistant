"""Document management router."""

import logging
import shutil
from pathlib import Path
from typing import List
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.models.chunk import Chunk
from app.models.document import Document, DocumentType
from app.schemas.document import (
    ChunkResponse,
    DocumentCreate,
    DocumentDetail,
    DocumentResponse,
)
from app.schemas.response import StatusResponse
from app.services.vector_store import get_vector_store
from app.tasks.document_processing import process_document_task
from app.utils.text_processing import sanitize_filename

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.post("/upload-url", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_url(
    doc_data: DocumentCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Upload and process a web article or YouTube video from URL.

    - **type**: Must be 'url' or 'youtube'
    - **url**: Valid HTTP/HTTPS URL
    - **title**: Optional custom title (auto-extracted if not provided)
    """
    if doc_data.type not in [DocumentType.URL, DocumentType.YOUTUBE]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Type must be 'url' or 'youtube' for URL upload",
        )

    if not doc_data.url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL is required",
        )

    try:
        # Create document record
        document = Document(
            type=doc_data.type,
            title=doc_data.title or "Processing...",
            author=doc_data.author,
            source_url=doc_data.url,
            doc_metadata=doc_data.metadata or {},
            processed=False,
        )

        db.add(document)
        await db.commit()
        await db.refresh(document)

        # Trigger async processing
        process_document_task.delay(str(document.id))

        logger.info(f"Created document {document.id} for URL: {doc_data.url}")

        return DocumentResponse(**document.to_dict())

    except Exception as e:
        logger.error(f"Error creating URL document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create document: {str(e)}",
        )


@router.post("/upload-pdf", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_pdf(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload and process a PDF file.

    - **file**: PDF file (max size configured in settings)
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed",
        )

    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning

    if file_size > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum of {settings.max_upload_size_mb}MB",
        )

    try:
        # Create upload directory
        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)

        # Save file
        file_id = uuid4()
        safe_filename = sanitize_filename(file.filename)
        file_path = upload_dir / f"{file_id}_{safe_filename}"

        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"Saved PDF file: {file_path}")

        # Create document record
        document = Document(
            type=DocumentType.PDF,
            title=safe_filename.replace('.pdf', ''),
            source_url=str(file_path),  # Store file path
            doc_metadata={"original_filename": file.filename, "file_size": file_size},
            processed=False,
        )

        db.add(document)
        await db.commit()
        await db.refresh(document)

        # Trigger async processing
        process_document_task.delay(str(document.id))

        logger.info(f"Created document {document.id} for PDF: {file.filename}")

        return DocumentResponse(**document.to_dict())

    except Exception as e:
        logger.error(f"Error uploading PDF: {e}")
        # Clean up file if document creation failed
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload PDF: {str(e)}",
        )


@router.post("/upload-text", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_text(
    doc_data: DocumentCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Upload plain text content.

    - **type**: Must be 'text'
    - **text**: Text content
    - **title**: Optional title
    """
    if doc_data.type != DocumentType.TEXT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Type must be 'text' for text upload",
        )

    if not doc_data.text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text content is required",
        )

    try:
        # Store text in metadata
        metadata = doc_data.metadata or {}
        metadata["content"] = doc_data.text

        # Create document record
        document = Document(
            type=DocumentType.TEXT,
            title=doc_data.title or "Text Document",
            author=doc_data.author,
            doc_metadata=metadata,
            processed=False,
        )

        db.add(document)
        await db.commit()
        await db.refresh(document)

        # Trigger async processing
        process_document_task.delay(str(document.id))

        logger.info(f"Created text document {document.id}")

        return DocumentResponse(**document.to_dict())

    except Exception as e:
        logger.error(f"Error creating text document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create text document: {str(e)}",
        )


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """
    List all documents.

    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    """
    try:
        result = await db.execute(
            select(Document)
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        documents = result.scalars().all()

        return [DocumentResponse(**doc.to_dict()) for doc in documents]

    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list documents",
        )


@router.get("/{document_id}", response_model=DocumentDetail)
async def get_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get document details with chunks.

    - **document_id**: Document UUID
    """
    try:
        result = await db.execute(
            select(Document)
            .options(selectinload(Document.chunks))
            .where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found",
            )

        # Convert to response
        doc_dict = document.to_dict()
        doc_dict["chunks"] = [ChunkResponse(**chunk.to_dict()) for chunk in document.chunks]

        return DocumentDetail(**doc_dict)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get document",
        )


@router.delete("/{document_id}", response_model=StatusResponse)
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a document and its chunks.

    - **document_id**: Document UUID
    """
    try:
        # Get document
        result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found",
            )

        # Delete from vector store
        vector_store = get_vector_store()
        vector_store.delete_by_document_id(str(document_id))

        # Delete PDF file if exists
        if document.type == DocumentType.PDF and document.source_url:
            file_path = Path(document.source_url)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted PDF file: {file_path}")

        # Delete from database (cascades to chunks)
        await db.delete(document)
        await db.commit()

        logger.info(f"Deleted document {document_id}")

        return StatusResponse(
            status="success",
            message=f"Document {document_id} deleted successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document",
        )
