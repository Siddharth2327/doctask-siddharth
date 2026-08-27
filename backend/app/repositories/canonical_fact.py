from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.canonical_fact import CanonicalFact
from app.repositories.base import Repository


class CanonicalFactRepository(Repository[CanonicalFact]):
    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get(self, entity_id: str) -> CanonicalFact | None:
        return self.db.get(CanonicalFact, UUID(entity_id))

    def get_by_field(
        self,
        case_id: str,
        field: str,
    ) -> CanonicalFact | None:
        statement = select(CanonicalFact).where(
            CanonicalFact.case_id == case_id,
            CanonicalFact.field == field,
        )

        return self.db.scalars(statement).first()

    def list_for_case(self, case_id: str) -> list[CanonicalFact]:
        statement = select(CanonicalFact).where(
            CanonicalFact.case_id == case_id
        )

        return list(self.db.scalars(statement).all())

    def upsert(
        self,
        *,
        case_id: str,
        field: str,
        value: str,
        evidence_id: UUID | None,
        document_version_id: UUID | None,
        run_id: str,
        finding_id: UUID | None,
    ) -> CanonicalFact:
        existing = self.get_by_field(case_id, field)

        if existing is not None:
            existing.value = value
            existing.evidence_id = evidence_id
            existing.document_version_id = document_version_id
            existing.run_id = run_id
            existing.finding_id = finding_id
            self.db.flush()

            return existing

        fact = CanonicalFact(
            id=uuid4(),
            case_id=case_id,
            field=field,
            value=value,
            evidence_id=evidence_id,
            document_version_id=document_version_id,
            run_id=run_id,
            finding_id=finding_id,
        )

        self.db.add(fact)
        self.db.flush()

        return fact
