from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.document import (
    DocumentVersionListResponse,
    DocumentVersionResponse,
    DocumentVersionUploadResponse,
    DocumentResponse,
    DocumentListResponse,
    DocumentSummaryResponse,
)
from app.services.document import DocumentService


router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)


@router.get(
    "",
    response_model=DocumentListResponse,
)
def list_documents(
    db: Session = Depends(get_db),
) -> DocumentListResponse:
    service = DocumentService(db)

    return DocumentListResponse(
        documents=[
            DocumentSummaryResponse.model_validate(document)
            for document in service.list_documents()
        ]
    )


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    name: str = Form(...),
    source: str = Form(...),
    db: Session = Depends(get_db),
) -> DocumentResponse:
    content = await file.read()

    service = DocumentService(db)

    document, version = service.upload_document(
        name=name,
        filename=file.filename or "unnamed",
        content_type=file.content_type or "application/octet-stream",
        source=source,
        content=content,
    )

    return DocumentResponse(
        id=document.id,
        name=document.name,
        source=document.source,
        created_at=document.created_at,
        version=version,
    )

@router.post(
    "/{document_id}/versions",
    response_model=DocumentVersionUploadResponse,
)
async def upload_version(
    document_id: UUID,
    file: UploadFile = File(...),
    source: str = Form(...),
    db: Session = Depends(get_db),
) -> DocumentVersionUploadResponse:
    content = await file.read()

    service = DocumentService(db)

    document, version, duplicate = service.upload_new_version(
        document_id=document_id,
        filename=file.filename or "unnamed",
        content_type=file.content_type or "application/octet-stream",
        source=source,
        content=content,
    )

    return DocumentVersionUploadResponse(
        version=version,
        is_duplicate=duplicate,
    )

@router.get(
    "/{document_id}/versions",
    response_model=DocumentVersionListResponse,
)
def list_versions(
    document_id: UUID,
    db: Session = Depends(get_db),
) -> DocumentVersionListResponse:
    service = DocumentService(db)

    versions = service.get_versions(document_id)

    return DocumentVersionListResponse(
        versions=versions,
    )

@router.get(
    "/{document_id}/versions/{version_id}",
    response_model=DocumentVersionResponse,
)
def get_version(
    document_id: UUID,
    version_id: UUID,
    db: Session = Depends(get_db),
) -> DocumentVersionResponse:
    service = DocumentService(db)

    return service.get_version(
        document_id,
        version_id,
    )