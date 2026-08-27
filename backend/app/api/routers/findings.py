from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.transaction import transaction
from app.schemas.run import (
    FindingDecisionRequest,
    FindingListResponse,
    FindingResponse,
)
from app.services.review import ReviewService



router = APIRouter(
    prefix="/findings",
    tags=["findings"],
)


@router.get("", response_model=FindingListResponse)
def list_findings(
    run_id: str | None = Query(default=None),
    case_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> FindingListResponse:
    service = ReviewService(db)

    findings = service.list_findings(run_id=run_id, case_id=case_id, status=status)

    return FindingListResponse(
        findings=[FindingResponse.from_model(f) for f in findings]
    )


@router.get("/{finding_id}", response_model=FindingResponse)
def get_finding(
    finding_id: UUID,
    db: Session = Depends(get_db),
) -> FindingResponse:
    service = ReviewService(db)

    return FindingResponse.from_model(service.get_finding(finding_id))

@router.post("/{finding_id}/decide", response_model=FindingResponse)
def decide_finding(
    finding_id: UUID,
    payload: FindingDecisionRequest,
    db: Session = Depends(get_db),
) -> FindingResponse:
    with transaction(db):
        service = ReviewService(db)

        finding = service.decide(
            finding_id,
            decision=payload.decision,
            reviewer=payload.reviewer,
            comment=payload.comment,
            edited_value=payload.edited_value,
        )

        response = FindingResponse.from_model(finding)

    return response