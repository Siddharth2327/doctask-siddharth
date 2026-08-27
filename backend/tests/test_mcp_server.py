from sqlalchemy import text

from app.core.config import settings
from app.db.session import SessionLocal, engine
from app.services.document import DocumentService

FIXTURES = "tests/fixtures/contract_corpus"


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


def test_mcp_tools_exist_and_are_registered():
    import asyncio

    from app.mcp.server import mcp

    tools = asyncio.run(mcp.list_tools())
    tool_names = {t.name for t in tools}

    assert tool_names == {
        "list_documents",
        "start_run",
        "get_run_status",
        "list_findings",
        "decide_finding",
        "finalize_review",
        "get_case_report",
    }


def test_mcp_full_flow_matches_service_layer(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "deterministic")
    cleanup()

    db = SessionLocal()

    try:
        document_service = DocumentService(db)

        with open(f"{FIXTURES}/contract_v1.txt", "rb") as handle:
            content = handle.read()

        document, version = document_service.upload_document(
            name="Acme Contract",
            filename="contract_v1.txt",
            content_type="text/plain",
            source="automated-test",
            content=content,
        )
        db.commit()

        document_id = str(document.id)
        version_id = str(version.id)
    finally:
        db.close()

    from app.mcp.server import (
        decide_finding,
        finalize_review,
        get_case_report,
        list_findings,
        start_run,
    )

    run_result = start_run(document_id, version_id, "CASE-MCP-001")
    assert run_result["status"] == "pending_review"

    findings = list_findings(run_id=run_result["run_id"])
    assert findings

    for finding in findings:
        decide_finding(
            finding["id"],
            decision="approved",
            reviewer="mcp-test@example.com",
        )

    commit_result = finalize_review(run_result["run_id"])
    assert commit_result["status"] == "completed"
    assert commit_result["committed"]

    report = get_case_report("CASE-MCP-001")
    fields = {f["field"] for f in report["facts"]}
    assert "vendor" in fields
    assert "contract_value" in fields
