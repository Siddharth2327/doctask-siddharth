from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.conflict import Conflict
from app.repositories.base import Repository


class ConflictRepository(Repository[Conflict]):
    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get(self, entity_id: str) -> Conflict | None:
        return self.db.get(Conflict, UUID(entity_id))

    def create(
        self,
        *,
        conflict_id: UUID,
        run_id: str,
        case_id: str,
        field: str,
        existing_value: str | None,
        existing_evidence_id: UUID | None,
        new_value: str,
        new_evidence_id: UUID | None,
        document_version_id: UUID,
    ) -> Conflict:
        conflict = Conflict(
            id=conflict_id,
            run_id=run_id,
            case_id=case_id,
            field=field,
            existing_value=existing_value,
            existing_evidence_id=existing_evidence_id,
            new_value=new_value,
            new_evidence_id=new_evidence_id,
            document_version_id=document_version_id,
            status="open",
        )

        self.db.add(conflict)
        self.db.flush()

        return conflict

    def list_for_run(self, run_id: str) -> list[Conflict]:
        statement = select(Conflict).where(Conflict.run_id == run_id)

        return list(self.db.scalars(statement).all())

    def list_for_case(self, case_id: str) -> list[Conflict]:
        statement = select(Conflict).where(Conflict.case_id == case_id)

        return list(self.db.scalars(statement).all())
