from datetime import datetime

from pydantic import BaseModel


class RunCreateRequest(BaseModel):
    document_id: str
    document_version_id: str
    case_id: str


class RunResponse(BaseModel):
    run_id: str
    case_id: str
    status: str
    facts: list[dict] | None = None
    conflicts: list[str] | None = None
    findings: list[str] | None = None
    errors: list[str] | None = None


class RunStatusResponse(BaseModel):
    run_id: str
    case_id: str
    document_id: str
    document_version_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost: float = 0.0


class FindingResponse(BaseModel):
    id: str
    run_id: str
    case_id: str
    type: str
    field: str | None
    proposed_value: str | None
    severity: str
    confidence: float | None
    evidence_ids: list[str]
    rationale: str
    status: str
    reviewer: str | None
    review_comment: str | None

    @classmethod
    def from_model(cls, finding) -> "FindingResponse":
        import json

        return cls(
            id=str(finding.id),
            run_id=finding.run_id,
            case_id=finding.case_id,
            type=finding.type,
            field=finding.field,
            proposed_value=finding.proposed_value,
            severity=finding.severity,
            confidence=finding.confidence,
            evidence_ids=json.loads(finding.evidence_ids),
            rationale=finding.rationale,
            status=finding.status,
            reviewer=finding.reviewer,
            review_comment=finding.review_comment,
        )


class FindingListResponse(BaseModel):
    findings: list[FindingResponse]


class FindingDecisionRequest(BaseModel):
    decision: str  # approved | rejected
    reviewer: str
    comment: str | None = None
    edited_value: str | None = None


class CommitResultResponse(BaseModel):
    run_id: str
    status: str
    committed: list[str]
    skipped_rejected: list[str]
    already_committed: list[str]
    still_pending: list[str]


class CanonicalFactResponse(BaseModel):
    field: str
    value: str
    evidence_id: str | None
    updated_at: datetime


class CaseReportResponse(BaseModel):
    case_id: str
    facts: list[CanonicalFactResponse]
