import time
from uuid import uuid4

import pymupdf
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.config import settings
from app.core.errors import AppError
from app.db.session import SessionLocal, engine
from app.main import app
from app.services.commit import CommitService
from app.services.document import DocumentService
from app.services.review import ReviewService
from app.services.run import RunService

FIXTURES = "tests/fixtures/contract_corpus"
client = TestClient(app)


def cleanup() -> None:
    with engine.begin() as connection:
        for table in (
            "commit_events",
            "canonical_facts",
            "findings",
            "conflicts",
            "chunks",
            "evidence",
            "runs",
            "document_versions",
            "documents",
        ):
            connection.execute(text(f"DELETE FROM {table}"))


@pytest.fixture(autouse=True)
def _use_deterministic_provider(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "deterministic")
    yield


def read_fixture(name: str) -> bytes:
    with open(f"{FIXTURES}/{name}", "rb") as handle:
        return handle.read()


def upload(db, filename: str, name: str):
    service = DocumentService(db)

    document, version = service.upload_document(
        name=name,
        filename=filename,
        content_type="text/plain",
        source="automated-test",
        content=read_fixture(filename),
    )
    db.commit()

    return document, version


def upload_new_version(db, document_id, filename: str):
    service = DocumentService(db)

    document, version, is_duplicate = service.upload_new_version(
        document_id=document_id,
        filename=filename,
        content_type="text/plain",
        source="automated-test",
        content=read_fixture(filename),
    )
    db.commit()

    return version


def approve_all_pending(db, run_id: str, reviewer: str = "reviewer@example.com"):
    review = ReviewService(db)

    for finding in review.list_findings(run_id=run_id, status="pending"):
        review.decide(
            finding.id,
            decision="approved",
            reviewer=reviewer,
        )
    db.commit()


# ----------------------------------------------------------------------
# T050/T051-T054: extraction, evidence, retrieval
# ----------------------------------------------------------------------

def test_run_produces_evidence_backed_facts_and_chunks():
    cleanup()
    db = SessionLocal()

    try:
        document, version = upload(db, "contract_v1.txt", "Acme Contract v1")

        run_service = RunService(db)
        result = run_service.run(
            document_id=document.id,
            document_version_id=version.id,
            case_id="CASE-ACME-001",
        )

        assert result["status"] == "pending_review"
        assert len(result["facts"]) >= 4  # vendor, contract_value, start_date, end_date, status

        from app.repositories.evidence import EvidenceRepository
        from app.repositories.chunk import ChunkRepository

        evidence_rows = EvidenceRepository(db).list_for_run(result["run_id"])
        assert len(evidence_rows) == len(result["facts"])
        assert all(row.quote for row in evidence_rows)

        chunks = ChunkRepository(db).list_for_version(version.id)
        assert len(chunks) >= 1
        assert all(c.embedding is not None for c in chunks)
    finally:
        db.close()


def test_retrieval_returns_relevant_chunk_for_query():
    cleanup()
    db = SessionLocal()

    try:
        document, version = upload(db, "contract_v1.txt", "Acme Contract v1")

        RunService(db).run(
            document_id=document.id,
            document_version_id=version.id,
            case_id="CASE-ACME-001",
        )

        from app.services.retrieval import RetrievalService

        retrieval = RetrievalService(db)
        results = retrieval.build_context(
            query="What is the contract value?",
            document_version_ids=[version.id],
            top_k=3,
        )

        assert len(results) >= 1
        assert any("Contract Value" in r.text for r in results)
    finally:
        db.close()


def test_run_persists_token_usage_estimate():
    cleanup()
    db = SessionLocal()

    try:
        document, version = upload(db, "contract_v1.txt", "Acme Contract v1")

        run_service = RunService(db)
        result = run_service.run(
            document_id=document.id,
            document_version_id=version.id,
            case_id="CASE-ACME-USAGE",
        )

        run = run_service.get_run(result["run_id"])

        # deterministic provider is an unpriced/free model -> cost stays 0.0,
        # but token counts must still be recorded from the graph's usage state.
        assert run["input_tokens"] > 0
        assert run["output_tokens"] > 0
        assert run["estimated_cost"] == 0.0
    finally:
        db.close()


def test_missing_document_raises_not_found():
    cleanup()
    db = SessionLocal()

    try:
        run_service = RunService(db)

        with pytest.raises(AppError) as exc_info:
            run_service.run(
                document_id=uuid4(),
                document_version_id=uuid4(),
                case_id="CASE-MISSING",
            )

        assert exc_info.value.status_code == 404
    finally:
        db.close()


# ----------------------------------------------------------------------
# T061/T063: deterministic rules and rule-violation findings
# ----------------------------------------------------------------------

def test_rule_violation_findings_for_incomplete_document():
    cleanup()
    db = SessionLocal()

    try:
        document, version = upload(db, "invoice.txt", "Acme Invoice")

        result = RunService(db).run(
            document_id=document.id,
            document_version_id=version.id,
            case_id="CASE-ACME-002",
        )

        from app.services.review import ReviewService

        findings = ReviewService(db).list_findings(run_id=result["run_id"])
        rule_findings = [f for f in findings if f.type == "rule_violation"]

        # invoice.txt has no contract_value -> required_field_present violation
        assert any(f.field == "contract_value" for f in rule_findings)
    finally:
        db.close()


def test_clean_corpus_yields_no_rule_violations():
    cleanup()
    db = SessionLocal()

    try:
        document, version = upload(db, "contract_v1.txt", "Acme Contract v1")

        result = RunService(db).run(
            document_id=document.id,
            document_version_id=version.id,
            case_id="CASE-ACME-003",
        )

        findings = ReviewService(db).list_findings(run_id=result["run_id"])
        rule_findings = [f for f in findings if f.type == "rule_violation"]

        assert rule_findings == []
    finally:
        db.close()


# ----------------------------------------------------------------------
# T060/T070/T071/T073: conflicts, partial review, idempotent commit
# ----------------------------------------------------------------------

def test_conflict_detection_reject_and_partial_approval():
    cleanup()
    db = SessionLocal()
    case_id = "CASE-ACME-004"

    try:
        # First run: establish the register.
        document, version = upload(db, "contract_v1.txt", "Acme Contract v1")
        first = RunService(db).run(
            document_id=document.id,
            document_version_id=version.id,
            case_id=case_id,
        )
        approve_all_pending(db, first["run_id"])
        commit1 = RunService(db).finalize_review(first["run_id"])
        assert commit1["status"] == "completed"
        assert len(commit1["committed"]) >= 1

        from app.repositories.canonical_fact import CanonicalFactRepository

        canonical = CanonicalFactRepository(db)
        contract_value_before = canonical.get_by_field(case_id, "contract_value").value
        assert contract_value_before == "100000"

        # Second run: a different document deliberately contradicts contract_value.
        renewal_doc, renewal_version = upload(
            db, "renewal_notice.txt", "Acme Renewal Notice"
        )
        second = RunService(db).run(
            document_id=renewal_doc.id,
            document_version_id=renewal_version.id,
            case_id=case_id,
        )
        assert len(second["conflicts"]) >= 1  # contract_value conflict

        review = ReviewService(db)
        findings = review.list_findings(run_id=second["run_id"])

        conflict_findings = [f for f in findings if f.type == "conflict"]
        assert any(f.field == "contract_value" for f in conflict_findings)

        # Reject the conflicting contract_value change; approve everything else.
        for finding in findings:
            if finding.type == "conflict" and finding.field == "contract_value":
                review.decide(
                    finding.id, decision="rejected", reviewer="reviewer@example.com"
                )
            else:
                review.decide(
                    finding.id, decision="approved", reviewer="reviewer@example.com"
                )
        db.commit()

        commit2 = RunService(db).finalize_review(second["run_id"])
        assert commit2["status"] == "completed"
        assert len(commit2["skipped_rejected"]) >= 1

        # The rejected contract_value must NOT have been committed.
        contract_value_after = canonical.get_by_field(case_id, "contract_value").value
        assert contract_value_after == "100000"

        # But the approved renewal_date IS committed (new field, no conflict).
        renewal_date = canonical.get_by_field(case_id, "renewal_date")
        assert renewal_date is not None
        assert renewal_date.value == "2027-01-01"
    finally:
        db.close()


def test_commit_is_idempotent():
    cleanup()
    db = SessionLocal()
    case_id = "CASE-ACME-005"

    try:
        document, version = upload(db, "contract_v1.txt", "Acme Contract v1")
        run_result = RunService(db).run(
            document_id=document.id,
            document_version_id=version.id,
            case_id=case_id,
        )
        approve_all_pending(db, run_result["run_id"])

        first_commit = RunService(db).finalize_review(run_result["run_id"])
        second_commit = RunService(db).finalize_review(run_result["run_id"])

        assert len(first_commit["committed"]) >= 1
        assert second_commit["committed"] == []
        assert set(second_commit["already_committed"]) == set(
            first_commit["committed"]
        )

        from app.repositories.commit_event import CommitEventRepository

        events = CommitEventRepository(db).list_for_run(run_result["run_id"])
        finding_ids = [str(e.finding_id) for e in events]
        assert len(finding_ids) == len(set(finding_ids))  # no duplicates
    finally:
        db.close()


def test_committed_finding_cannot_be_re_decided():
    cleanup()
    db = SessionLocal()
    case_id = "CASE-ACME-006"

    try:
        document, version = upload(db, "contract_v1.txt", "Acme Contract v1")
        run_result = RunService(db).run(
            document_id=document.id,
            document_version_id=version.id,
            case_id=case_id,
        )
        approve_all_pending(db, run_result["run_id"])
        RunService(db).finalize_review(run_result["run_id"])

        review = ReviewService(db)
        committed = review.list_findings(run_id=run_result["run_id"], status="committed")
        assert committed

        with pytest.raises(AppError) as exc_info:
            review.decide(
                committed[0].id,
                decision="rejected",
                reviewer="reviewer@example.com",
            )

        assert exc_info.value.code == "FINDING_ALREADY_COMMITTED"
    finally:
        db.close()


# ----------------------------------------------------------------------
# T072: durable checkpoint / crash-resume
# ----------------------------------------------------------------------

def test_workflow_checkpoint_persists_between_sessions():
    cleanup()
    db = SessionLocal()
    case_id = "CASE-ACME-007"

    try:
        document, version = upload(db, "contract_v1.txt", "Acme Contract v1")
        run_result = RunService(db).run(
            document_id=document.id,
            document_version_id=version.id,
            case_id=case_id,
        )
        run_id = run_result["run_id"]
    finally:
        db.close()

    # Simulate a fresh process: new DB session, new checkpointer connection,
    # inspecting the SAME thread_id after the "crash".
    from app.agents.checkpoint import create_checkpointer
    from app.agents.workflow import build_workflow

    with create_checkpointer() as checkpointer:
        workflow = build_workflow(checkpointer)
        config = {"configurable": {"thread_id": run_id}}
        state = workflow.get_state(config)

        assert state.values.get("extracted_facts")
        assert state.values.get("run_id") == run_id

    # Resume review + commit in a brand-new session, proving the run can be
    # finalized without ever holding the original in-memory objects.
    db2 = SessionLocal()

    try:
        approve_all_pending(db2, run_id)
        result = RunService(db2).finalize_review(run_id)
        assert result["status"] == "completed"
    finally:
        db2.close()


# ----------------------------------------------------------------------
# T090-T092: incremental update
# ----------------------------------------------------------------------

def test_incremental_update_preserves_unaffected_fields():
    cleanup()
    db = SessionLocal()
    case_id = "CASE-ACME-008"

    try:
        document, version = upload(db, "contract_v1.txt", "Acme Contract v1")
        first = RunService(db).run(
            document_id=document.id,
            document_version_id=version.id,
            case_id=case_id,
        )
        approve_all_pending(db, first["run_id"])
        RunService(db).finalize_review(first["run_id"])

        from app.repositories.canonical_fact import CanonicalFactRepository

        canonical = CanonicalFactRepository(db)
        start_date_before = canonical.get_by_field(case_id, "start_date")
        vendor_before = canonical.get_by_field(case_id, "vendor")

        # New version: end_date genuinely changes, everything else identical.
        new_version = upload_new_version(db, document.id, "contract_v2_amendment.txt")

        second = RunService(db).run_incremental_update(
            document_id=document.id,
            document_version_id=new_version.id,
            case_id=case_id,
        )

        review = ReviewService(db)
        findings = review.list_findings(run_id=second["run_id"])
        fields_with_findings = {f.field for f in findings}

        # Only end_date should have produced a new finding -- vendor and
        # start_date are unchanged and must be silently skipped.
        assert "end_date" in fields_with_findings
        assert "vendor" not in fields_with_findings
        assert "start_date" not in fields_with_findings

        approve_all_pending(db, second["run_id"])
        RunService(db).finalize_review(second["run_id"])

        start_date_after = canonical.get_by_field(case_id, "start_date")
        vendor_after = canonical.get_by_field(case_id, "vendor")
        end_date_after = canonical.get_by_field(case_id, "end_date")

        assert start_date_after.value == start_date_before.value
        assert start_date_after.updated_at == start_date_before.updated_at
        assert vendor_after.value == vendor_before.value
        assert end_date_after.value == "2027-06-30"
    finally:
        db.close()


# ----------------------------------------------------------------------
# Prompt injection resistance (T100 series requirement, applied here)
# ----------------------------------------------------------------------

def test_prompt_injection_fixture_produces_no_facts():
    """A document containing an injection attempt has no 'Label: value'
    lines the deterministic extractor recognizes, so it must yield zero
    facts rather than following any embedded instruction."""

    from app.agents.extraction import StructuredExtractionService
    from app.integrations.ai.deterministic import DeterministicKeyValueAIProvider

    with open("tests/fixtures/prompt_injection_document.txt") as handle:
        content = handle.read()

    provider = DeterministicKeyValueAIProvider()
    service = StructuredExtractionService(provider)

    result, _, _ = service.extract(
        document_id="doc-injection",
        document_version_id="v-injection",
        content=content,
        model="deterministic-v1",
    )

    assert result.facts == []


# ----------------------------------------------------------------------
# Page-aware evidence references (Phase B)
# ----------------------------------------------------------------------

def build_two_page_pdf_bytes() -> bytes:
    document = pymupdf.open()

    page1 = document.new_page()
    page1.insert_text((72, 72), "Vendor: Acme Supplies")

    page2 = document.new_page()
    page2.insert_text((72, 72), "Contract Value: 100000")

    content = document.tobytes()
    document.close()

    return content


def test_evidence_location_reflects_real_pdf_page():
    cleanup()
    db = SessionLocal()

    try:
        service = DocumentService(db)

        document, version = service.upload_document(
            name="Two Page PDF Contract",
            filename="contract.pdf",
            content_type="application/pdf",
            source="automated-test",
            content=build_two_page_pdf_bytes(),
        )
        db.commit()

        result = RunService(db).run(
            document_id=document.id,
            document_version_id=version.id,
            case_id="CASE-ACME-PDF-PAGES",
        )

        from app.repositories.evidence import EvidenceRepository

        evidence_rows = EvidenceRepository(db).list_for_run(result["run_id"])
        evidence_by_field = {row.field: row for row in evidence_rows}

        assert evidence_by_field["vendor"].location == "page 1"
        assert evidence_by_field["contract_value"].location == "page 2"
    finally:
        db.close()


# ----------------------------------------------------------------------
# Phase C: GET /documents (used by the frontend's Documents page)
# ----------------------------------------------------------------------

def test_list_documents_api():
    cleanup()
    db = SessionLocal()

    try:
        upload(db, "contract_v1.txt", "Acme Contract v1")
        upload(db, "invoice.txt", "Acme Invoice")
    finally:
        db.close()

    response = client.get("/documents")

    assert response.status_code == 200
    names = {d["name"] for d in response.json()["documents"]}
    assert names == {"Acme Contract v1", "Acme Invoice"}

def test_run_with_conflicts_serializes_correctly_via_api():
    """Regression test: RunService.run() must return conflict ids as
    strings, not UUID objects -- RunResponse.conflicts is list[str] and
    Pydantic will reject raw UUIDs at the API boundary. This only
    surfaces via the actual HTTP endpoint, not by calling
    RunService.run() directly, so this test goes through the client."""

    cleanup()
    db = SessionLocal()
    case_id = "CASE-ACME-API-CONFLICT"

    try:
        document, version = upload(db, "contract_v1.txt", "Acme Contract v1")
        first = RunService(db).run(
            document_id=document.id,
            document_version_id=version.id,
            case_id=case_id,
        )
        approve_all_pending(db, first["run_id"])
        RunService(db).finalize_review(first["run_id"])

        renewal_doc, renewal_version = upload(
            db, "renewal_notice.txt", "Acme Renewal Notice"
        )
    finally:
        db.close()

    response = client.post(
        "/runs",
        json={
            "document_id": str(renewal_doc.id),
            "document_version_id": str(renewal_version.id),
            "case_id": case_id,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["conflicts"]) >= 1
    assert all(isinstance(c, str) for c in body["conflicts"])