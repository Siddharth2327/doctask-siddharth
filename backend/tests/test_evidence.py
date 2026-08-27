from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.errors import AppError
from app.db.session import SessionLocal, engine
from app.main import app
from app.repositories.document import DocumentRepository
from app.services.evidence import EvidenceService


client = TestClient(app)


def cleanup() -> None:
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM evidence"))
        connection.execute(text("DELETE FROM document_versions"))
        connection.execute(text("DELETE FROM documents"))


def create_document_and_version(db):
    repository = DocumentRepository(db)

    document = repository.create_document(
        document_id=uuid4(),
        name="Vendor Contract",
        source="automated-test",
    )

    version = repository.create_version(
        version_id=uuid4(),
        document_id=document.id,
        version_number=1,
        parent_version_id=None,
        filename="contract.txt",
        content_type="text/plain",
        content_hash="a" * 64,
        source="automated-test",
        storage_reference=None,
    )

    db.commit()

    return document, version


def sample_facts(document_id, version_id):
    return [
        {
            "field": "contract_value",
            "value": 100000,
            "confidence": 0.95,
            "evidence": [
                {
                    "document_id": str(document_id),
                    "document_version_id": str(version_id),
                    "location": "page 1",
                    "chunk_id": None,
                    "quote": "The total contract value is $100,000.",
                }
            ],
        },
        {
            "field": "vendor",
            "value": "Acme Supplies",
            "confidence": 0.9,
            "evidence": [
                {
                    "document_id": str(document_id),
                    "document_version_id": str(version_id),
                    "location": "page 1",
                    "chunk_id": None,
                    "quote": "This agreement is between Acme Supplies and the buyer.",
                }
            ],
        },
    ]


def test_persist_facts_evidence_creates_one_row_per_reference():
    cleanup()
    db = SessionLocal()

    try:
        document, version = create_document_and_version(db)

        service = EvidenceService(db)

        persisted = service.persist_facts_evidence(
            run_id="run-001",
            document_id=document.id,
            document_version_id=version.id,
            facts=sample_facts(document.id, version.id),
        )
        db.commit()

        assert len(persisted) == 2

        stored = service.get_for_document(document.id)

        assert len(stored) == 2
        assert {row.field for row in stored} == {
            "contract_value",
            "vendor",
        }
        assert all(row.run_id == "run-001" for row in stored)
        assert all(row.document_version_id == version.id for row in stored)
        assert all(row.quote for row in stored)
    finally:
        db.close()


def test_persist_facts_evidence_unknown_document_raises():
    cleanup()
    db = SessionLocal()

    try:
        service = EvidenceService(db)
        missing_document_id = uuid4()

        with pytest.raises(AppError) as exc_info:
            service.persist_facts_evidence(
                run_id="run-001",
                document_id=missing_document_id,
                document_version_id=uuid4(),
                facts=sample_facts(missing_document_id, uuid4()),
            )

        assert exc_info.value.code == "DOCUMENT_NOT_FOUND"
    finally:
        db.close()


def test_get_for_run_filters_by_run_id():
    cleanup()
    db = SessionLocal()

    try:
        document, version = create_document_and_version(db)

        service = EvidenceService(db)

        service.persist_facts_evidence(
            run_id="run-A",
            document_id=document.id,
            document_version_id=version.id,
            facts=sample_facts(document.id, version.id)[:1],
        )
        service.persist_facts_evidence(
            run_id="run-B",
            document_id=document.id,
            document_version_id=version.id,
            facts=sample_facts(document.id, version.id)[1:],
        )
        db.commit()

        run_a_evidence = service.get_for_run("run-A")
        run_b_evidence = service.get_for_run("run-B")

        assert len(run_a_evidence) == 1
        assert run_a_evidence[0].field == "contract_value"

        assert len(run_b_evidence) == 1
        assert run_b_evidence[0].field == "vendor"
    finally:
        db.close()


def test_list_evidence_for_document_api():
    cleanup()
    db = SessionLocal()

    try:
        document, version = create_document_and_version(db)

        service = EvidenceService(db)
        service.persist_facts_evidence(
            run_id="run-001",
            document_id=document.id,
            document_version_id=version.id,
            facts=sample_facts(document.id, version.id),
        )
        db.commit()
    finally:
        db.close()

    response = client.get(f"/documents/{document.id}/evidence")

    assert response.status_code == 200

    body = response.json()

    assert len(body["evidence"]) == 2
    assert body["evidence"][0]["document_id"] == str(document.id)


def test_list_evidence_for_unknown_document_returns_404():
    cleanup()

    response = client.get(f"/documents/{uuid4()}/evidence")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DOCUMENT_NOT_FOUND"


def test_list_evidence_for_run_api():
    cleanup()
    db = SessionLocal()

    try:
        document, version = create_document_and_version(db)

        service = EvidenceService(db)
        service.persist_facts_evidence(
            run_id="run-run-endpoint",
            document_id=document.id,
            document_version_id=version.id,
            facts=sample_facts(document.id, version.id),
        )
        db.commit()
    finally:
        db.close()

    response = client.get("/runs/run-run-endpoint/evidence")

    assert response.status_code == 200
    assert len(response.json()["evidence"]) == 2
