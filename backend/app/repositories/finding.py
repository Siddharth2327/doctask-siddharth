import json
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.finding import Finding
from app.repositories.base import Repository


class FindingRepository(Repository[Finding]):
    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get(self, entity_id: str) -> Finding | None:
        return self.db.get(Finding, UUID(entity_id))

    def create(
        self,
        *,
        finding_id: UUID,
        run_id: str,
        case_id: str,
        type: str,
        field: str | None,
        proposed_value: str | None,
        severity: str,
        confidence: float | None,
        evidence_ids: list[str],
        rationale: str,
        conflict_id: UUID | None = None,
    ) -> Finding:
        finding = Finding(
            id=finding_id,
            run_id=run_id,
            case_id=case_id,
            type=type,
            field=field,
            proposed_value=proposed_value,
            severity=severity,
            confidence=confidence,
            evidence_ids=json.dumps([str(e) for e in evidence_ids]),
            rationale=rationale,
            conflict_id=conflict_id,
            status="pending",
        )

        self.db.add(finding)
        self.db.flush()

        return finding

    def list_for_run(
        self,
        run_id: str,
        status: str | None = None,
    ) -> list[Finding]:
        statement = select(Finding).where(Finding.run_id == run_id)

        if status:
            statement = statement.where(Finding.status == status)

        statement = statement.order_by(Finding.created_at.asc())

        return list(self.db.scalars(statement).all())

    def list_for_case(
        self,
        case_id: str,
        status: str | None = None,
    ) -> list[Finding]:
        statement = select(Finding).where(Finding.case_id == case_id)

        if status:
            statement = statement.where(Finding.status == status)

        return list(self.db.scalars(statement).all())

    def decide(
        self,
        finding_id: UUID,
        *,
        decision: str,
        reviewer: str | None,
        comment: str | None,
        edited_value: str | None = None,
    ) -> Finding | None:
        finding = self.db.get(Finding, finding_id)

        if finding is None:
            return None

        finding.status = decision
        finding.reviewer = reviewer
        finding.review_comment = comment
        finding.reviewed_at = datetime.now(timezone.utc)

        if edited_value is not None:
            finding.proposed_value = edited_value

        self.db.flush()

        return finding
