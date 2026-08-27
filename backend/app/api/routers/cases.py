from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.canonical_fact import CanonicalFactRepository
from app.schemas.run import CanonicalFactResponse, CaseReportResponse


router = APIRouter(
    prefix="/cases",
    tags=["cases"],
)


@router.get("/{case_id}/report", response_model=CaseReportResponse)
def get_case_report(
    case_id: str,
    db: Session = Depends(get_db),
) -> CaseReportResponse:
    repository = CanonicalFactRepository(db)

    facts = repository.list_for_case(case_id)

    return CaseReportResponse(
        case_id=case_id,
        facts=[
            CanonicalFactResponse(
                field=fact.field,
                value=fact.value,
                evidence_id=str(fact.evidence_id) if fact.evidence_id else None,
                updated_at=fact.updated_at,
            )
            for fact in facts
        ],
    )
