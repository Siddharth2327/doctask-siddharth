from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.repositories.document import DocumentRepository
from app.repositories.evidence import EvidenceRepository


class EvidenceService:
    """Application service for evidence persistence and retrieval.

    This is the extension point where in-memory `ExtractedFact.evidence`
    references produced during a workflow run (see
    app.agents.extraction.ExtractedFact) become durable, queryable
    `Evidence` rows. It is intentionally decoupled from the LangGraph
    node functions in app.agents.workflow: nodes stay pure and
    DB-free (and therefore cheaply unit-testable), while the caller
    that drives a run — the future run/orchestration service (T054 /
    T070) — is responsible for calling `persist_facts_evidence` once
    a document/version and run_id are known to exist.
    """

    def __init__(self, db: Session) -> None:
        self.repository = EvidenceRepository(db)
        self.document_repository = DocumentRepository(db)

    def persist_facts_evidence(
        self,
        *,
        run_id: str,
        document_id: UUID,
        document_version_id: UUID,
        facts: list[dict[str, Any]],
    ) -> list:
        """Persist evidence attached to a batch of extracted facts.

        `facts` is the same shape produced by extract_node's
        `extracted_facts` state list: each item has a `field` and an
        `evidence` list of dicts with document_id/document_version_id/
        location/chunk_id/quote.
        """

        document = self.document_repository.get(str(document_id))

        if document is None:
            raise AppError(
                code="DOCUMENT_NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        persisted = []

        for fact in facts:
            field = fact.get("field")

            for reference in fact.get("evidence", []):
                evidence = self.repository.create(
                    evidence_id=uuid4(),
                    run_id=run_id,
                    document_id=document_id,
                    document_version_id=document_version_id,
                    field=field,
                    location=reference.get("location"),
                    chunk_id=reference.get("chunk_id"),
                    quote=reference.get("quote"),
                )

                persisted.append(evidence)

        return persisted

    def get_for_document(
        self,
        document_id: UUID,
    ) -> list:
        document = self.document_repository.get(str(document_id))

        if document is None:
            raise AppError(
                code="DOCUMENT_NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        return self.repository.list_for_document(document_id)

    def get_for_run(
        self,
        run_id: str,
    ) -> list:
        return self.repository.list_for_run(run_id)
