from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.evidence import Evidence
from app.repositories.base import Repository


class EvidenceRepository(Repository[Evidence]):
    """Repository for evidence persistence operations."""

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get(self, entity_id: str) -> Evidence | None:
        return self.db.get(Evidence, UUID(entity_id))

    def create(
        self,
        *,
        evidence_id: UUID,
        run_id: str,
        document_id: UUID,
        document_version_id: UUID,
        field: str | None = None,
        location: str | None = None,
        chunk_id: str | None = None,
        quote: str | None = None,
    ) -> Evidence:
        evidence = Evidence(
            id=evidence_id,
            run_id=run_id,
            document_id=document_id,
            document_version_id=document_version_id,
            field=field,
            location=location,
            chunk_id=chunk_id,
            quote=quote,
        )

        self.db.add(evidence)
        self.db.flush()

        return evidence

    def list_for_document(
        self,
        document_id: UUID,
    ) -> list[Evidence]:
        statement = (
            select(Evidence)
            .where(Evidence.document_id == document_id)
            .order_by(Evidence.created_at.asc())
        )

        return list(self.db.scalars(statement).all())

    def list_for_run(
        self,
        run_id: str,
    ) -> list[Evidence]:
        statement = (
            select(Evidence)
            .where(Evidence.run_id == run_id)
            .order_by(Evidence.created_at.asc())
        )

        return list(self.db.scalars(statement).all())
