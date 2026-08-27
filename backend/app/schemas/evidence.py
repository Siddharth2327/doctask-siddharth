from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    run_id: str
    document_id: UUID
    document_version_id: UUID
    field: str | None
    location: str | None
    chunk_id: str | None
    quote: str | None
    created_at: datetime


class EvidenceListResponse(BaseModel):
    evidence: list[EvidenceResponse]
