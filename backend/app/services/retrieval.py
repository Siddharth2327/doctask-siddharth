from dataclasses import dataclass
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.chunking.chunker import chunk_document
from app.integrations.embeddings.base import EmbeddingProvider
from app.integrations.embeddings.factory import create_embedding_provider
from app.parsing.models import ParsedDocument
from app.repositories.chunk import ChunkRepository


@dataclass(frozen=True)
class RetrievedContext:
    """A single ranked piece of grounded context, with its source
    reference preserved end to end (T054: "preserve source references")."""

    chunk_id: UUID
    document_id: UUID
    document_version_id: UUID
    page_index: int | None
    text: str
    distance: float


class RetrievalService:
    """Application service for chunking, embedding, and retrieval.

    This is the T051-T054 vertical slice: parsed document -> persisted,
    embedded chunks -> pgvector similarity search -> ranked, source-
    attributed context. Kept intentionally simple per TASK.md guidance:
    no re-ranking model, no hybrid search, no chunk-overlap tuning.
    """

    def __init__(
        self,
        db: Session,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:
        self.db = db
        self.repository = ChunkRepository(db)
        self.embedding_provider = (
            embedding_provider or create_embedding_provider()
        )

    def chunk_and_embed_version(
        self,
        *,
        document_id: UUID,
        document_version_id: UUID,
        parsed_document: ParsedDocument,
    ) -> list:
        """Chunk + embed a document version, persisting the result.

        Idempotent: if this version has already been chunked, existing
        chunks are returned unchanged rather than duplicated. This is
        what makes it safe to call on every run of a document,
        including incremental re-processing (T090+) where the same
        unchanged version may be revisited.
        """

        if self.repository.has_chunks_for_version(document_version_id):
            return self.repository.list_for_version(document_version_id)

        chunks = chunk_document(
            parsed_document,
            document_version_id=str(document_version_id),
        )

        if not chunks:
            return []

        embeddings = self.embedding_provider.embed(
            [chunk.text for chunk in chunks]
        )

        persisted = []

        for chunk, embedding in zip(chunks, embeddings):
            persisted.append(
                self.repository.create(
                    chunk_id=uuid4(),
                    document_id=document_id,
                    document_version_id=document_version_id,
                    chunk_index=chunk.index,
                    page_index=chunk.page_index,
                    chunk_hash=chunk.chunk_hash,
                    text=chunk.text,
                    embedding=embedding,
                )
            )

        return persisted

    def build_context(
        self,
        *,
        query: str,
        document_version_ids: list[UUID] | None = None,
        top_k: int = 5,
    ) -> list[RetrievedContext]:
        """Retrieve the top-k chunks most relevant to `query`."""

        query_embedding = self.embedding_provider.embed([query])[0]

        results = self.repository.search(
            query_embedding=query_embedding,
            top_k=top_k,
            document_version_ids=document_version_ids,
        )

        return [
            RetrievedContext(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                document_version_id=chunk.document_version_id,
                page_index=chunk.page_index,
                text=chunk.text,
                distance=distance,
            )
            for chunk, distance in results
        ]

    def find_best_chunk_for_quote(
        self,
        *,
        quote: str,
        document_version_id: UUID,
    ) -> RetrievedContext | None:
        """Ground a piece of extracted evidence text against the chunk
        it most likely came from, restricted to its source version.

        Used to resolve `Evidence.chunk_id` after extraction: the LLM
        (or the deterministic demo provider) returns a quote, and this
        finds which persisted chunk that quote belongs to.
        """

        results = self.build_context(
            query=quote,
            document_version_ids=[document_version_id],
            top_k=1,
        )

        return results[0] if results else None
