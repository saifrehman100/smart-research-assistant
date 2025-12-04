"""Document processing Celery tasks."""

import asyncio
import logging
from pathlib import Path
from typing import Dict
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session_maker
from app.models.chunk import Chunk
from app.models.document import Document, DocumentType
from app.services.chunker import get_chunker
from app.services.embedding_service import get_embedding_service
from app.services.ingestion import (
    PDFParser,
    TextProcessor,
    WebScraper,
    YouTubeExtractor,
)
from app.services.vector_store import get_vector_store
from app.tasks import celery_app

logger = logging.getLogger(__name__)


async def _process_document_async(document_id: str) -> Dict:
    """
    Async function to process a document.

    Args:
        document_id: Document UUID as string

    Returns:
        Processing result dictionary
    """
    session_maker = get_session_maker()

    async with session_maker() as db:
        try:
            # Fetch document
            result = await db.execute(
                select(Document).where(Document.id == UUID(document_id))
            )
            document = result.scalar_one_or_none()

            if not document:
                raise ValueError(f"Document not found: {document_id}")

            logger.info(f"Processing document: {document.title} ({document.type})")

            # Extract content based on type
            content_data = None

            if document.type == DocumentType.URL:
                scraper = WebScraper()
                content_data = await scraper.scrape(document.source_url)

            elif document.type == DocumentType.PDF:
                parser = PDFParser()
                # Assume source_url contains file path for PDF
                content_data = await parser.parse(document.source_url)

            elif document.type == DocumentType.YOUTUBE:
                extractor = YouTubeExtractor()
                content_data = await extractor.extract(document.source_url)

            elif document.type == DocumentType.TEXT:
                processor = TextProcessor()
                # For text type, content is stored in metadata
                text_content = document.doc_metadata.get("content", "")
                content_data = await processor.process(
                    text=text_content,
                    title=document.title,
                    author=document.author,
                )

            if not content_data:
                raise Exception("Failed to extract content from document")

            # Chunk the content
            chunker = get_chunker()

            # Check if document has page information (PDF)
            if "pages" in content_data:
                chunks_data = chunker.chunk_document_with_pages(
                    pages=content_data["pages"],
                    source_metadata={
                        "document_id": str(document.id),
                        "title": document.title,
                        "type": document.type.value,
                        "source_url": document.source_url,
                    },
                )
            else:
                # Use clean_content for YouTube if available (without timestamps)
                content = content_data.get("clean_content", content_data["content"])

                chunks_data = chunker.chunk_text(
                    text=content,
                    source_metadata={
                        "document_id": str(document.id),
                        "title": document.title,
                        "type": document.type.value,
                        "source_url": document.source_url,
                    },
                )

            if not chunks_data:
                raise Exception("No chunks created from document")

            logger.info(f"Created {len(chunks_data)} chunks")

            # Generate embeddings
            embedding_service = get_embedding_service()
            chunk_texts = [chunk["content"] for chunk in chunks_data]
            embeddings = await embedding_service.generate_embeddings(chunk_texts)

            logger.info(f"Generated {len(embeddings)} embeddings")

            # Store in vector database
            vector_store = get_vector_store()
            chunk_ids = vector_store.add_documents(
                embeddings=embeddings,
                texts=chunk_texts,
                metadatas=[chunk["metadata"] for chunk in chunks_data],
            )

            logger.info(f"Stored {len(chunk_ids)} chunks in vector store")

            # Save chunks to database
            for i, (chunk_data, embedding_id) in enumerate(zip(chunks_data, chunk_ids)):
                chunk = Chunk(
                    document_id=document.id,
                    content=chunk_data["content"],
                    chunk_index=i,
                    embedding_id=embedding_id,
                    chunk_metadata=chunk_data["metadata"],
                )
                db.add(chunk)

            # Mark document as processed
            document.processed = True

            # Update metadata with extraction info
            document.doc_metadata.update(
                {
                    "chunks_count": len(chunks_data),
                    "total_characters": len(content_data["content"]),
                    **content_data.get("metadata", {}),
                }
            )

            await db.commit()

            logger.info(f"Successfully processed document: {document.title}")

            return {
                "status": "success",
                "document_id": str(document.id),
                "chunks_created": len(chunks_data),
            }

        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            await db.rollback()

            # Mark document as failed
            try:
                result = await db.execute(
                    select(Document).where(Document.id == UUID(document_id))
                )
                document = result.scalar_one_or_none()
                if document:
                    document.doc_metadata["processing_error"] = str(e)
                    document.processed = False
                    await db.commit()
            except Exception as update_error:
                logger.error(f"Error updating document status: {update_error}")

            raise


@celery_app.task(name="process_document", bind=True, max_retries=3)
def process_document_task(self, document_id: str) -> Dict:
    """
    Celery task to process a document.

    Args:
        document_id: Document UUID as string

    Returns:
        Processing result dictionary
    """
    try:
        # Run async function in event loop
        result = asyncio.run(_process_document_async(document_id))
        return result

    except Exception as e:
        logger.error(f"Task error processing document {document_id}: {e}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
