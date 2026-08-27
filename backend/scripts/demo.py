"""Docsnary vertical-slice demo.

Exercises the real application layers end to end against the contract
register domain (T100): evidence-backed extraction, retrieval,
conflict detection, deterministic rule validation, findings, human
review (partial approval), idempotent commit, durable
checkpoint/crash-resume, incremental update, and the MCP adapter.

No paid API key required -- uses the deterministic key/value AI
provider and the deterministic embedding provider.

Usage (from the backend/ directory, with Postgres + Redis running):

    docker-compose up -d
    alembic upgrade head
    python scripts/demo.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.repositories.canonical_fact import CanonicalFactRepository  # noqa: E402
from app.services.document import DocumentService  # noqa: E402
from app.services.retrieval import RetrievalService  # noqa: E402
from app.services.review import ReviewService  # noqa: E402
from app.services.run import RunService  # noqa: E402

FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "contract_corpus"
CASE_ID = "CASE-ACME-DEMO"
MCP_CASE_ID = "CASE-ACME-DEMO-MCP"


def banner(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def step(title: str) -> None:
    print()
    print(f"--- {title} ---")


def cleanup_demo_data() -> None:
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


def read_fixture(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def upload(db, filename: str, display_name: str):
    service = DocumentService(db)

    document, version = service.upload_document(
        name=display_name,
        filename=filename,
        content_type="text/plain",
        source="demo",
        content=read_fixture(filename),
    )
    db.commit()

    print(f"Uploaded '{display_name}' -> document_id={document.id} version_id={version.id}")

    return document, version


def print_findings(db, run_id: str) -> list:
    findings = ReviewService(db).list_findings(run_id=run_id)

    for finding in findings:
        print(
            f"  [{finding.type:<12}] field={finding.field!s:<16} "
            f"proposed={finding.proposed_value!r:<20} "
            f"severity={finding.severity:<6} status={finding.status}"
        )

    return findings


def print_register(db, case_id: str) -> None:
    facts = CanonicalFactRepository(db).list_for_case(case_id)

    if not facts:
        print("  (register is empty)")
        return

    for fact in sorted(facts, key=lambda f: f.field):
        print(f"  {fact.field:<16} = {fact.value}")


def approve(db, run_id: str, *, only_field: str | None = None, exclude_field: str | None = None):
    review = ReviewService(db)

    for finding in review.list_findings(run_id=run_id, status="pending"):
        if only_field is not None and finding.field != only_field:
            continue

        if exclude_field is not None and finding.field == exclude_field:
            review.decide(finding.id, decision="rejected", reviewer="demo-reviewer")
            continue

        review.decide(finding.id, decision="approved", reviewer="demo-reviewer")

    db.commit()


def main() -> None:
    settings.ai_provider = "deterministic"

    banner("DOCSNARY VERTICAL SLICE DEMO")
    print(f"AI provider: {settings.ai_provider} (offline, deterministic)")
    print(f"Embedding provider: {settings.embedding_provider} (offline, deterministic)")

    cleanup_demo_data()

    # ------------------------------------------------------------------
    step("1) Ingest the initial contract and run the full pipeline")
    db = SessionLocal()
    document, version = upload(db, "contract_v1.txt", "Acme Master Services Agreement")

    run_service = RunService(db)
    result = run_service.run(
        document_id=document.id,
        document_version_id=version.id,
        case_id=CASE_ID,
    )
    run1_id = result["run_id"]
    print(f"Run {run1_id} -> status={result['status']}, facts extracted={len(result['facts'])}")

    step("Findings generated (all pending human review)")
    print_findings(db, run1_id)

    step("2) Human review: approve everything")
    approve(db, run1_id)

    step("3) Commit approved findings")
    commit1 = run_service.finalize_review(run1_id)
    print(f"Committed: {commit1['committed']}")
    print(f"Skipped (rejected): {commit1['skipped_rejected']}")

    step("Canonical register after run 1")
    print_register(db, CASE_ID)

    # ------------------------------------------------------------------
    step("4) Retrieval: ground a question against persisted, embedded chunks")
    retrieval = RetrievalService(db)
    hits = retrieval.build_context(
        query="What is the contract value?",
        document_version_ids=[version.id],
        top_k=2,
    )
    for hit in hits:
        print(f"  distance={hit.distance:.4f}  chunk_id={hit.chunk_id}  text={hit.text!r}")

    # ------------------------------------------------------------------
    step("5) Ingest a renewal notice with a DELIBERATE contradiction ($120,000 vs $100,000)")
    renewal_doc, renewal_version = upload(db, "renewal_notice.txt", "Acme Renewal Notice")

    result2 = run_service.run(
        document_id=renewal_doc.id,
        document_version_id=renewal_version.id,
        case_id=CASE_ID,
    )
    run2_id = result2["run_id"]
    print(f"Run {run2_id} -> conflicts detected: {len(result2['conflicts'])}")

    step("Findings generated for run 2 (conflict + new fields)")
    print_findings(db, run2_id)

    step("6) Human review: REJECT the bad $120,000 contract_value, approve everything else")
    approve(db, run2_id, exclude_field="contract_value")

    step("7) Commit run 2")
    commit2 = run_service.finalize_review(run2_id)
    print(f"Committed: {commit2['committed']}")
    print(f"Skipped (rejected): {commit2['skipped_rejected']}")

    step("Canonical register after run 2 -- contract_value must STILL be 100000")
    print_register(db, CASE_ID)

    # ------------------------------------------------------------------
    step("8) Commit is idempotent: finalize the same run again")
    commit2_again = run_service.finalize_review(run2_id)
    print(f"Newly committed this time: {commit2_again['committed']} (expected: [])")
    print(f"Already committed (skipped): {commit2_again['already_committed']}")

    # ------------------------------------------------------------------
    step("9) Durable checkpoint / crash-resume: inspect run 1's LangGraph state "
         "from a brand-new session/connection, as if this were a new process")
    db.close()

    from app.agents.checkpoint import create_checkpointer
    from app.agents.workflow import build_workflow

    with create_checkpointer() as checkpointer:
        workflow = build_workflow(checkpointer)
        state = workflow.get_state({"configurable": {"thread_id": run1_id}})
        print(f"Recovered checkpoint for run {run1_id}:")
        print(f"  status={state.values.get('status')}  review_status={state.values.get('review_status')}")
        print(f"  extracted_facts persisted: {len(state.values.get('extracted_facts', []))}")

    db = SessionLocal()

    # ------------------------------------------------------------------
    step("10) Incremental update: a new version of the contract extends end_date only")
    new_version_result = DocumentService(db).upload_new_version(
        document_id=document.id,
        filename="contract_v2_amendment.txt",
        content_type="text/plain",
        source="demo",
        content=read_fixture("contract_v2_amendment.txt"),
    )
    _, new_version, _ = new_version_result
    db.commit()
    print(f"New version uploaded -> version_id={new_version.id}")

    result3 = run_service.run_incremental_update(
        document_id=document.id,
        document_version_id=new_version.id,
        case_id=CASE_ID,
    )
    run3_id = result3["run_id"]

    step("Findings for the incremental run (only end_date should appear as new/changed)")
    print_findings(db, run3_id)

    approve(db, run3_id)
    run_service.finalize_review(run3_id)

    step("Canonical register after incremental update")
    print_register(db, CASE_ID)

    # ------------------------------------------------------------------
    step("11) Docsnary MCP: the same workflow, via the MCP tool functions")
    from app.mcp import server as mcp_server

    mcp_doc, mcp_version = upload(db, "invoice.txt", "Acme Invoice (via MCP)")
    db.close()

    mcp_run = mcp_server.start_run(str(mcp_doc.id), str(mcp_version.id), MCP_CASE_ID)
    print(f"MCP start_run -> {mcp_run['status']}, run_id={mcp_run['run_id']}")

    for finding in mcp_server.list_findings(run_id=mcp_run["run_id"]):
        mcp_server.decide_finding(
            finding["id"], decision="approved", reviewer="mcp-demo-reviewer"
        )

    mcp_commit = mcp_server.finalize_review(mcp_run["run_id"])
    print(f"MCP finalize_review -> committed={mcp_commit['committed']}")

    mcp_report = mcp_server.get_case_report(MCP_CASE_ID)
    print("MCP get_case_report ->")
    for fact in mcp_report["facts"]:
        print(f"  {fact['field']:<16} = {fact['value']}")

    banner("DEMO COMPLETE")
    print(
        "Run the resilience test suite with:\n"
        "  pytest tests/test_vertical_slice.py tests/test_mcp_server.py "
        "tests/test_run_queue.py tests/test_evidence.py -v"
    )


if __name__ == "__main__":
    main()
