"""Docsnary MCP server.

IMPORTANT (per project guidance): this module contains NO domain
logic of its own. Every tool below opens a database session and
delegates directly to the same application services used by the
REST API (app.services.run, app.services.review, app.services.commit,
app.services.document, app.repositories.canonical_fact). If a tool
needs new behavior, add it to the relevant service, not here.

Run with:
    python -m app.mcp.server
"""

from uuid import UUID

from mcp.server.fastmcp import FastMCP

from app.db.session import SessionLocal
from app.repositories.canonical_fact import CanonicalFactRepository
from app.schemas.run import FindingResponse
from app.services.document import DocumentService
from app.services.review import ReviewService
from app.services.run import RunService

mcp = FastMCP(
    name="docsnary",
    instructions=(
        "Tools for running Docsnary's evidence-backed document "
        "analysis workflow: start a run, inspect findings, record "
        "human review decisions, and read the committed case report."
    ),
)


@mcp.tool()
def list_documents() -> list[dict]:
    """List all uploaded documents."""

    db = SessionLocal()

    try:
        service = DocumentService(db)

        return [
            {
                "id": str(document.id),
                "name": document.name,
                "source": document.source,
            }
            for document in service.list_documents()
        ]
    finally:
        db.close()


@mcp.tool()
def start_run(document_id: str, document_version_id: str, case_id: str) -> dict:
    """Run a document version through evidence extraction, retrieval,
    conflict detection, and rule validation, producing findings that
    are ready for human review. Does not commit anything."""

    db = SessionLocal()

    try:
        service = RunService(db)

        return service.run(
            document_id=UUID(document_id),
            document_version_id=UUID(document_version_id),
            case_id=case_id,
        )
    finally:
        db.close()


@mcp.tool()
def get_run_status(run_id: str) -> dict:
    """Get a run's current status."""

    db = SessionLocal()

    try:
        service = RunService(db)

        run = service.get_run(run_id)
        run["created_at"] = str(run["created_at"])
        run["updated_at"] = str(run["updated_at"])

        return run
    finally:
        db.close()


@mcp.tool()
def list_findings(
    run_id: str | None = None,
    case_id: str | None = None,
    status: str | None = None,
) -> list[dict]:
    """List findings for a run or case, optionally filtered by status
    (pending | approved | rejected | committed)."""

    db = SessionLocal()

    try:
        service = ReviewService(db)

        findings = service.list_findings(
            run_id=run_id, case_id=case_id, status=status
        )

        return [FindingResponse.from_model(f).model_dump() for f in findings]
    finally:
        db.close()


@mcp.tool()
def decide_finding(
    finding_id: str,
    decision: str,
    reviewer: str,
    comment: str | None = None,
    edited_value: str | None = None,
) -> dict:
    """Approve or reject a single finding (decision: "approved" or
    "rejected"). Optionally override the proposed value via
    edited_value before approving."""

    db = SessionLocal()

    try:
        service = ReviewService(db)

        finding = service.decide(
            UUID(finding_id),
            decision=decision,
            reviewer=reviewer,
            comment=comment,
            edited_value=edited_value,
        )
        db.commit()

        return FindingResponse.from_model(finding).model_dump()
    finally:
        db.close()


@mcp.tool()
def finalize_review(run_id: str) -> dict:
    """Commit all approved findings for a run (rejected findings are
    never committed; pending findings are left for later). Safe to
    call more than once -- already-committed findings are skipped."""

    db = SessionLocal()

    try:
        service = RunService(db)

        return service.finalize_review(run_id)
    finally:
        db.close()


@mcp.tool()
def get_case_report(case_id: str) -> dict:
    """Return the committed, evidence-linked canonical register for a
    case -- the current believed truth for every field, each traceable
    to the evidence and finding that produced it."""

    db = SessionLocal()

    try:
        repository = CanonicalFactRepository(db)

        facts = repository.list_for_case(case_id)

        return {
            "case_id": case_id,
            "facts": [
                {
                    "field": fact.field,
                    "value": fact.value,
                    "evidence_id": (
                        str(fact.evidence_id) if fact.evidence_id else None
                    ),
                    "updated_at": str(fact.updated_at),
                }
                for fact in facts
            ],
        }
    finally:
        db.close()


if __name__ == "__main__":
    mcp.run()
