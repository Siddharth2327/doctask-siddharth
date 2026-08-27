from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.repositories.base import Repository


class ChunkRepository(Repository[Chunk]):
    """Repository for chunk persistence and pgvector retrieval."""

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get(self, entity_id: str) -> Chunk | None:
        return self.db.get(Chunk, UUID(entity_id))

    def create(
        self,
        *,
        chunk_id: UUID,
        document_id: UUID,
        document_version_id: UUID,
        chunk_index: int,
        page_index: int | None,
        chunk_hash: str,
        text: str,
        embedding: list[float] | None,
    ) -> Chunk:
        chunk = Chunk(
            id=chunk_id,
            document_id=document_id,
            document_version_id=document_version_id,
            chunk_index=chunk_index,
            page_index=page_index,
            chunk_hash=chunk_hash,
            text=text,
            embedding=embedding,
        )

        self.db.add(chunk)
        self.db.flush()

        return chunk

    def list_for_version(
        self,
        document_version_id: UUID,
    ) -> list[Chunk]:
        statement = (
            select(Chunk)
            .where(Chunk.document_version_id == document_version_id)
            .order_by(Chunk.chunk_index.asc())
        )

        return list(self.db.scalars(statement).all())

    def has_chunks_for_version(
        self,
        document_version_id: UUID,
    ) -> bool:
        statement = select(Chunk.id).where(
            Chunk.document_version_id == document_version_id
        ).limit(1)

        return self.db.scalars(statement).first() is not None

    def search(
        self,
        *,
        query_embedding: list[float],
        top_k: int = 5,
        document_version_ids: list[UUID] | None = None,
    ) -> list[tuple[Chunk, float]]:
        """Return the top-k chunks closest to `query_embedding` by
        cosine distance (lower is more similar), optionally restricted
        to a set of document versions (e.g. all versions in a case).
        """

        distance = Chunk.embedding.cosine_distance(query_embedding)

        statement = select(Chunk, distance.label("distance"))

        if document_version_ids:
            statement = statement.where(
                Chunk.document_version_id.in_(document_version_ids)
            )

        statement = statement.order_by(distance.asc()).limit(top_k)

        return [(row[0], row[1]) for row in self.db.execute(statement).all()]
