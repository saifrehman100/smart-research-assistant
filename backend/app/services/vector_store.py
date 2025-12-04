"""Vector store service using ChromaDB."""

import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """Vector store for storing and retrieving embeddings using ChromaDB."""

    def __init__(self):
        """Initialize ChromaDB vector store."""
        # Ensure persist directory exists
        persist_dir = Path(settings.chroma_persist_directory)
        persist_dir.mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB persistent client
        self.client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=ChromaSettings(
                anonymized_telemetry=False,
            )
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_collection_name,
            metadata={"description": "Research assistant document embeddings"},
        )

        logger.info(
            f"Vector store initialized with collection: {settings.chroma_collection_name}"
        )

    def add_documents(
        self,
        embeddings: List[List[float]],
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Add documents with embeddings to the vector store.

        Args:
            embeddings: List of embedding vectors
            texts: List of text contents
            metadatas: List of metadata dictionaries
            ids: Optional list of IDs (generated if not provided)

        Returns:
            List of document IDs
        """
        if not embeddings or not texts:
            raise ValueError("Embeddings and texts cannot be empty")

        if len(embeddings) != len(texts) or len(embeddings) != len(metadatas):
            raise ValueError("Embeddings, texts, and metadatas must have same length")

        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in range(len(embeddings))]

        try:
            # Convert all metadata values to strings for ChromaDB
            processed_metadatas = []
            for metadata in metadatas:
                processed = {}
                for key, value in metadata.items():
                    if value is None:
                        processed[key] = ""
                    elif isinstance(value, (list, dict)):
                        processed[key] = str(value)
                    else:
                        processed[key] = str(value)
                processed_metadatas.append(processed)

            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=processed_metadatas,
                ids=ids,
            )

            logger.info(f"Added {len(ids)} documents to vector store")
            return ids

        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
            raise

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict:
        """
        Search for similar documents.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            filters: Optional metadata filters

        Returns:
            Dictionary with ids, documents, metadatas, and distances
        """
        try:
            # Build where clause for filtering
            where_clause = None
            if filters:
                where_clause = {}
                for key, value in filters.items():
                    if value is not None:
                        where_clause[key] = str(value)

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_clause,
            )

            # Process results
            if not results["ids"] or not results["ids"][0]:
                return {
                    "ids": [],
                    "documents": [],
                    "metadatas": [],
                    "distances": [],
                }

            return {
                "ids": results["ids"][0],
                "documents": results["documents"][0],
                "metadatas": results["metadatas"][0],
                "distances": results["distances"][0],
            }

        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            raise

    def delete_by_document_id(self, document_id: str) -> None:
        """
        Delete all chunks for a document.

        Args:
            document_id: Document ID to delete chunks for
        """
        try:
            # Query all chunks for this document
            results = self.collection.get(
                where={"document_id": str(document_id)},
            )

            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                logger.info(
                    f"Deleted {len(results['ids'])} chunks for document {document_id}"
                )

        except Exception as e:
            logger.error(f"Error deleting document chunks: {e}")
            raise

    def delete(self, ids: List[str]) -> None:
        """
        Delete specific documents by IDs.

        Args:
            ids: List of document IDs to delete
        """
        try:
            self.collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents from vector store")
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            raise

    def get_collection_stats(self) -> Dict:
        """
        Get statistics about the collection.

        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.collection.count()
            return {
                "name": self.collection.name,
                "count": count,
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"name": self.collection.name, "count": 0}


# Global vector store instance
_vector_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    """Get or create vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
