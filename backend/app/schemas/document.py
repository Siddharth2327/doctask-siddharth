from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    parent_version_id: UUID | None
    version_number: int
    filename: str
    content_type: str
    content_hash: str
    source: str
    storage_reference: str | None
    created_at: datetime


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    source: str
    created_at: datetime
    version: DocumentVersionResponse

class DocumentVersionListResponse(BaseModel):
    versions: list[DocumentVersionResponse]


class DocumentSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    source: str
    created_at: datetime


class DocumentListResponse(BaseModel):
    documents: list[DocumentSummaryResponse]


class DocumentVersionUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    version: DocumentVersionResponse
    is_duplicate: bool