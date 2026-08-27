from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.commit_event import CommitEvent
from app.repositories.base import Repository


class CommitEventRepository(Repository[CommitEvent]):
    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get(self, entity_id: str) -> CommitEvent | None:
        return self.db.get(CommitEvent, UUID(entity_id))

    def get_for_finding(self, finding_id: UUID) -> CommitEvent | None:
        statement = select(CommitEvent).where(
            CommitEvent.finding_id == finding_id
        )

        return self.db.scalars(statement).first()

    def create(
        self,
        *,
        finding_id: UUID,
        run_id: str,
        case_id: str,
        field: str | None,
        value: str | None,
        action: str,
    ) -> CommitEvent:
        event = CommitEvent(
            id=uuid4(),
            finding_id=finding_id,
            run_id=run_id,
            case_id=case_id,
            field=field,
            value=value,
            action=action,
        )

        self.db.add(event)
        self.db.flush()

        return event

    def list_for_run(self, run_id: str) -> list[CommitEvent]:
        statement = select(CommitEvent).where(CommitEvent.run_id == run_id)

        return list(self.db.scalars(statement).all())
