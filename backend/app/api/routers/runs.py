from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.run import RunCreateRequest, RunResponse, RunStatusResponse
from app.services.run import RunService


router = APIRouter(
    prefix="/runs",
    tags=["runs"],
)


@router.post("", response_model=RunResponse)
def create_run(
    payload: RunCreateRequest,
    db: Session = Depends(get_db),
) -> RunResponse:
    service = RunService(db)

    result = service.run(
        document_id=UUID(payload.document_id),
        document_version_id=UUID(payload.document_version_id),
        case_id=payload.case_id,
    )

    return RunResponse(**result)


@router.get("/{run_id}", response_model=RunStatusResponse)
def get_run(
    run_id: str,
    db: Session = Depends(get_db),
) -> RunStatusResponse:
    service = RunService(db)

    return RunStatusResponse(**service.get_run(run_id))


@router.post("/{run_id}/finalize")
def finalize_run(
    run_id: str,
    db: Session = Depends(get_db),
) -> dict:
    service = RunService(db)

    return service.finalize_review(run_id)
