from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.canonical_fact import CanonicalFactRepository
from app.repositories.commit_event import CommitEventRepository
from app.repositories.finding import FindingRepository


class CommitService:
    """Application service for committing reviewed findings (T073).

    Rules enforced here, not left to the caller:
    - Only APPROVED findings are ever written to CanonicalFact.
    - REJECTED findings are recorded in the audit trail but never
      change the register.
    - PENDING findings are left untouched (not yet decided).
    - Commit is idempotent: a finding that already has a CommitEvent
      is skipped rather than re-applied, so calling commit_run twice
      never double-writes or duplicates audit history.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.finding_repository = FindingRepository(db)
        self.canonical_repository = CanonicalFactRepository(db)
        self.commit_event_repository = CommitEventRepository(db)

    def commit_run(self, run_id: str) -> dict:
        findings = self.finding_repository.list_for_run(run_id)

        committed = []
        skipped_rejected = []
        already_committed = []
        still_pending = []

        for finding in findings:
            existing_event = self.commit_event_repository.get_for_finding(
                finding.id
            )

            if existing_event is not None:
                already_committed.append(str(finding.id))
                continue

            if finding.status == "pending":
                still_pending.append(str(finding.id))
                continue

            if finding.status == "rejected":
                self.commit_event_repository.create(
                    finding_id=finding.id,
                    run_id=run_id,
                    case_id=finding.case_id,
                    field=finding.field,
                    value=None,
                    action="skipped_rejected",
                )
                skipped_rejected.append(str(finding.id))
                continue

            if finding.status == "approved":
                evidence_id = self._primary_evidence_id(finding)

                if finding.field and finding.proposed_value is not None:
                    self.canonical_repository.upsert(
                        case_id=finding.case_id,
                        field=finding.field,
                        value=finding.proposed_value,
                        evidence_id=evidence_id,
                        document_version_id=None,
                        run_id=run_id,
                        finding_id=finding.id,
                    )

                self.commit_event_repository.create(
                    finding_id=finding.id,
                    run_id=run_id,
                    case_id=finding.case_id,
                    field=finding.field,
                    value=finding.proposed_value,
                    action="committed",
                )

                finding.status = "committed"
                self.db.flush()

                committed.append(str(finding.id))

        return {
            "run_id": run_id,
            "committed": committed,
            "skipped_rejected": skipped_rejected,
            "already_committed": already_committed,
            "still_pending": still_pending,
        }

    @staticmethod
    def _primary_evidence_id(finding) -> UUID | None:
        import json

        evidence_ids = json.loads(finding.evidence_ids)

        return UUID(evidence_ids[0]) if evidence_ids else None
