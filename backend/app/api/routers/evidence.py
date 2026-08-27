from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.evidence import EvidenceListResponse
from app.services.evidence import EvidenceService


router = APIRouter(
    prefix="/documents",
    tags=["evidence"],
)


@router.get(
    "/{document_id}/evidence",
    response_model=EvidenceListResponse,
)
def list_evidence_for_document(
    document_id: UUID,
    db: Session = Depends(get_db),
) -> EvidenceListResponse:
    service = EvidenceService(db)

    evidence = service.get_for_document(document_id)

    return EvidenceListResponse(evidence=evidence)


runs_router = APIRouter(
    prefix="/runs",
    tags=["evidence"],
)


@runs_router.get(
    "/{run_id}/evidence",
    response_model=EvidenceListResponse,
)
def list_evidence_for_run(
    run_id: str,
    db: Session = Depends(get_db),
) -> EvidenceListResponse:
    service = EvidenceService(db)

    evidence = service.get_for_run(run_id)

    return EvidenceListResponse(evidence=evidence)
