from uuid import UUID

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.repositories.finding import FindingRepository

VALID_DECISIONS = {"approved", "rejected"}


class ReviewService:
    """Application service for the human review gate (T070/T071/T072).

    Review is item-level by design: approving or rejecting one finding
    never affects another. This service only records the decision;
    RunService/CommitService are responsible for advancing the
    workflow and committing once a run's findings are decided.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = FindingRepository(db)

    def list_findings(
        self,
        *,
        run_id: str | None = None,
        case_id: str | None = None,
        status: str | None = None,
    ):
        if run_id:
            return self.repository.list_for_run(run_id, status=status)

        if case_id:
            return self.repository.list_for_case(case_id, status=status)

        raise AppError(
            code="MISSING_FILTER",
            message="Either run_id or case_id must be provided",
            status_code=400,
        )

    def get_finding(self, finding_id: UUID):
        finding = self.repository.get(str(finding_id))

        if finding is None:
            raise AppError(
                code="FINDING_NOT_FOUND",
                message="Finding not found",
                status_code=404,
            )

        return finding

    def decide(
        self,
        finding_id: UUID,
        *,
        decision: str,
        reviewer: str,
        comment: str | None = None,
        edited_value: str | None = None,
    ):
        if decision not in VALID_DECISIONS:
            raise AppError(
                code="INVALID_DECISION",
                message=f"Decision must be one of {sorted(VALID_DECISIONS)}",
                status_code=400,
            )

        finding = self.get_finding(finding_id)

        if finding.status == "committed":
            raise AppError(
                code="FINDING_ALREADY_COMMITTED",
                message="This finding has already been committed and can no longer be changed.",
                status_code=409,
            )

        updated = self.repository.decide(
            finding.id,
            decision=decision,
            reviewer=reviewer,
            comment=comment,
            edited_value=edited_value,
        )

        return updated

    def run_review_summary(self, run_id: str) -> dict:
        findings = self.repository.list_for_run(run_id)

        return {
            "total": len(findings),
            "pending": sum(1 for f in findings if f.status == "pending"),
            "approved": sum(1 for f in findings if f.status == "approved"),
            "rejected": sum(1 for f in findings if f.status == "rejected"),
            "committed": sum(1 for f in findings if f.status == "committed"),
        }
