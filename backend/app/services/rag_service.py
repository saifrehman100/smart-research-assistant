"""RAG (Retrieval Augmented Generation) service."""

import logging
from datetime import datetime
from typing import AsyncGenerator, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.conversation import Conversation
from app.models.document import Document
from app.models.message import Message, MessageRole
from app.schemas.query import SourceReference
from app.services.embedding_service import get_embedding_service
from app.services.gemini_client import get_gemini_client
from app.services.vector_store import get_vector_store

logger = logging.getLogger(__name__)


class RAGService:
    """Service for RAG-based question answering."""

    SYSTEM_PROMPT = """You are a helpful research assistant. Answer questions based ONLY on the provided context from the sources below.

IMPORTANT GUIDELINES:
1. Always cite your sources using this format: [Source: Title, Page/Timestamp]
2. If the context doesn't contain enough information to answer the question, say "I don't have enough information in the provided sources to answer this question."
3. Be concise but comprehensive
4. Use direct quotes when appropriate
5. If multiple sources say similar things, cite all relevant sources
6. Do not make up information or use knowledge outside the provided context

When citing:
- For PDFs: [Source: Document Title, Page X]
- For web articles: [Source: Article Title]
- For YouTube videos: [Source: Video Title, Timestamp]
"""

    def __init__(self):
        """Initialize RAG service."""
        self.gemini_client = get_gemini_client()
        self.embedding_service = get_embedding_service()
        self.vector_store = get_vector_store()

    async def _retrieve_relevant_chunks(
        self,
        query: str,
        top_k: int = None,
        filters: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Retrieve relevant document chunks for a query.

        Args:
            query: Search query
            top_k: Number of chunks to retrieve
            filters: Optional metadata filters

        Returns:
            List of chunk dictionaries with metadata
        """
        top_k = top_k or settings.top_k_retrieval

        # Generate query embedding
        query_embedding = await self.embedding_service.generate_query_embedding(query)

        # Search vector store
        results = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filters=filters,
        )

        # Convert to structured format
        chunks = []
        for i, chunk_id in enumerate(results["ids"]):
            # Convert distance to similarity score (lower distance = higher similarity)
            distance = results["distances"][i]
            similarity_score = 1 / (1 + distance)  # Normalize to 0-1 range

            chunks.append({
                "id": chunk_id,
                "content": results["documents"][i],
                "metadata": results["metadatas"][i],
                "relevance_score": similarity_score,
            })

        logger.info(f"Retrieved {len(chunks)} relevant chunks for query")
        return chunks

    async def _get_document_info(
        self, document_id: UUID, db: AsyncSession
    ) -> Optional[Dict]:
        """
        Get document information from database.

        Args:
            document_id: Document UUID
            db: Database session

        Returns:
            Document info dictionary or None
        """
        try:
            result = await db.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()

            if document:
                return document.to_dict()
            return None
        except Exception as e:
            logger.error(f"Error fetching document {document_id}: {e}")
            return None

    async def _build_context(
        self, chunks: List[Dict], db: AsyncSession
    ) -> tuple[str, List[SourceReference]]:
        """
        Build context string and source references from chunks.

        Args:
            chunks: List of chunk dictionaries
            db: Database session

        Returns:
            Tuple of (context_string, source_references)
        """
        # Filter chunks by relevance threshold
        relevant_chunks = [
            c for c in chunks
            if c["relevance_score"] >= settings.relevance_threshold
        ]

        # Limit to top K context chunks
        relevant_chunks = relevant_chunks[:settings.top_k_context]

        if not relevant_chunks:
            return "", []

        # Build context string
        context_parts = ["CONTEXT FROM SOURCES:\n"]
        sources = []
        seen_docs = set()

        for i, chunk in enumerate(relevant_chunks, 1):
            metadata = chunk["metadata"]
            doc_id = metadata.get("document_id")

            # Get document info if not already fetched
            if doc_id and doc_id not in seen_docs:
                doc_info = await self._get_document_info(UUID(doc_id), db)
                if doc_info:
                    seen_docs.add(doc_id)

                    # Create source reference
                    source_ref = SourceReference(
                        document_id=UUID(doc_id),
                        title=doc_info["title"],
                        type=doc_info["type"],
                        author=doc_info.get("author"),
                        url=doc_info.get("source_url"),
                        chunk_content=chunk["content"][:200] + "...",
                        relevance_score=chunk["relevance_score"],
                        page_number=int(metadata.get("page_number", 0))
                        if metadata.get("page_number")
                        else None,
                        timestamp=metadata.get("timestamp"),
                    )
                    sources.append(source_ref)

            # Add to context
            source_label = metadata.get("title", "Unknown Source")
            page_info = ""
            if metadata.get("page_number"):
                page_info = f", Page {metadata.get('page_number')}"

            context_parts.append(
                f"\n[Source {i}: {source_label}{page_info}]\n{chunk['content']}\n"
            )

        context_string = "\n".join(context_parts)
        return context_string, sources

    async def _get_conversation_history(
        self, conversation_id: UUID, db: AsyncSession, limit: int = None
    ) -> str:
        """
        Get recent conversation history.

        Args:
            conversation_id: Conversation UUID
            db: Database session
            limit: Maximum number of messages to retrieve

        Returns:
            Formatted conversation history
        """
        limit = limit or settings.max_conversation_history

        try:
            result = await db.execute(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.desc())
                .limit(limit * 2)  # Get both user and assistant messages
            )
            messages = result.scalars().all()

            if not messages:
                return ""

            # Reverse to chronological order
            messages = list(reversed(messages))

            history_parts = ["CONVERSATION HISTORY:\n"]
            for msg in messages:
                role = "User" if msg.role == MessageRole.USER else "Assistant"
                history_parts.append(f"{role}: {msg.content}\n")

            return "\n".join(history_parts)

        except Exception as e:
            logger.error(f"Error fetching conversation history: {e}")
            return ""

    async def answer_question(
        self,
        question: str,
        conversation_id: Optional[UUID],
        db: AsyncSession,
    ) -> Dict:
        """
        Answer a question using RAG.

        Args:
            question: User question
            conversation_id: Optional conversation ID for context
            db: Database session

        Returns:
            Dictionary with answer, sources, and conversation info
        """
        logger.info(f"Answering question: {question[:100]}...")

        # Retrieve relevant chunks
        chunks = await self._retrieve_relevant_chunks(question)

        # Build context from chunks
        context, sources = await self._build_context(chunks, db)

        if not context:
            answer = "I don't have enough information in the provided sources to answer this question. Please add relevant documents first."

            # Create or get conversation
            if not conversation_id:
                title = question[:100] if len(question) <= 100 else question[:97] + "..."
                conversation = Conversation(title=title)
                db.add(conversation)
                await db.flush()
                conversation_id = conversation.id
            else:
                result = await db.execute(
                    select(Conversation).where(Conversation.id == conversation_id)
                )
                conversation = result.scalar_one_or_none()
                if conversation:
                    conversation.updated_at = datetime.utcnow()

            # Save user message
            user_message = Message(
                conversation_id=conversation_id,
                role=MessageRole.USER,
                content=question,
                sources=[],
            )
            db.add(user_message)

            # Save assistant message
            assistant_message = Message(
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,
                content=answer,
                sources=[],
            )
            db.add(assistant_message)

            await db.commit()

            return {
                "answer": answer,
                "sources": [],
                "conversation_id": conversation_id,
                "message_id": assistant_message.id,
                "created_at": assistant_message.created_at,
            }

        # Get conversation history if exists
        conversation_history = ""
        if conversation_id:
            conversation_history = await self._get_conversation_history(
                conversation_id, db
            )

        # Build full prompt
        full_context = f"{self.SYSTEM_PROMPT}\n\n{conversation_history}\n\n{context}"

        # Generate answer
        answer = await self.gemini_client.generate_response(
            prompt=question,
            context=full_context,
        )

        # Create or get conversation
        if not conversation_id:
            # Create new conversation
            # Generate title from question
            title = question[:100] if len(question) <= 100 else question[:97] + "..."

            conversation = Conversation(title=title)
            db.add(conversation)
            await db.flush()
            conversation_id = conversation.id
        else:
            # Update existing conversation
            result = await db.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()
            if conversation:
                conversation.updated_at = datetime.utcnow()

        # Save user message
        user_message = Message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=question,
            sources=[],
        )
        db.add(user_message)

        # Save assistant message
        assistant_message = Message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=answer,
            sources=[source.model_dump(mode='json') for source in sources],
        )
        db.add(assistant_message)

        await db.commit()

        return {
            "answer": answer,
            "sources": sources,
            "conversation_id": conversation_id,
            "message_id": assistant_message.id,
            "created_at": assistant_message.created_at,
        }

    async def answer_question_stream(
        self,
        question: str,
        conversation_id: Optional[UUID],
        db: AsyncSession,
    ) -> AsyncGenerator[str, None]:
        """
        Answer a question using RAG with streaming response.

        Args:
            question: User question
            conversation_id: Optional conversation ID for context
            db: Database session

        Yields:
            Chunks of the answer
        """
        logger.info(f"Answering question (streaming): {question[:100]}...")

        # Retrieve relevant chunks
        chunks = await self._retrieve_relevant_chunks(question)

        # Build context from chunks
        context, sources = await self._build_context(chunks, db)

        if not context:
            yield "I don't have enough information in the provided sources to answer this question."
            return

        # Get conversation history if exists
        conversation_history = ""
        if conversation_id:
            conversation_history = await self._get_conversation_history(
                conversation_id, db
            )

        # Build full prompt
        full_context = f"{self.SYSTEM_PROMPT}\n\n{conversation_history}\n\n{context}"

        # Generate streaming answer
        full_answer = ""
        async for chunk in self.gemini_client.generate_response_stream(
            prompt=question,
            context=full_context,
        ):
            full_answer += chunk
            yield chunk

        # Save to database after streaming completes
        # Create or get conversation
        if not conversation_id:
            title = question[:100] if len(question) <= 100 else question[:97] + "..."
            conversation = Conversation(title=title)
            db.add(conversation)
            await db.flush()
            conversation_id = conversation.id

        # Save messages
        user_message = Message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=question,
            sources=[],
        )
        db.add(user_message)

        assistant_message = Message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=full_answer,
            sources=[source.model_dump(mode='json') for source in sources],
        )
        db.add(assistant_message)

        await db.commit()


def get_rag_service() -> RAGService:
    """Get RAG service instance."""
    return RAGService()
