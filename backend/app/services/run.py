from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.agents.checkpoint import create_checkpointer
from app.agents.workflow import build_workflow
from app.core.errors import AppError
from app.db.transaction import transaction
from app.integrations.ai.base import AIProvider
from app.integrations.ai.factory import create_ai_provider
from app.integrations.embeddings.base import EmbeddingProvider
from app.repositories.run import RunRepository
from app.rules.engine import run_rules
from app.services.commit import CommitService
from app.services.conflict import ConflictService
from app.services.document import DocumentService
from app.services.evidence import EvidenceService
from app.services.finding import FindingService
from app.services.retrieval import RetrievalService


def _initial_agent_state(
    *,
    run_id: str,
    document_id: str,
    document_version_id: str,
    parsed_content: str,
) -> dict:
    return {
        "run_id": run_id,
        "document_id": document_id,
        "document_version_id": document_version_id,
        "parsed_content": parsed_content,
        "status": "pending",
        "extracted_facts": [],
        "evidence": [],
        "conflicts": [],
        "validation_results": [],
        "findings": [],
        "proposed_changes": [],
        "review_status": "pending",
        "retry_state": {
            "attempt": 0,
            "max_attempts": 3,
            "reason": None,
            "escalated": False,
        },
        "errors": [],
        "usage": {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "estimated_cost": 0.0,
        },
        "prompt_metadata": [],
    }


class RunService:
    """Orchestrates one end-to-end analysis run.

    This is the coherent integration point the LangGraph node functions
    deliberately do NOT contain (they stay pure and DB-free so they
    remain cheap, isolated unit tests -- see app.agents.workflow and
    tests/test_agent_workflow.py). RunService is what turns those pure
    building blocks into an actual working system:

        parse -> chunk/embed -> extract (via the graph, checkpointed)
              -> persist evidence -> detect conflicts -> run rules
              -> generate findings -> pause for human review

    and, once findings are decided:

        commit approved findings -> resume the graph to reflect completion

    The LangGraph checkpoint (thread_id == run_id) proves durable
    workflow state and crash/resume (T072); the `runs` table plus the
    domain tables (evidence/conflicts/findings/canonical_facts) are
    the ordinary, immediately-committed source of truth for the API.
    """

    def __init__(
        self,
        db: Session,
        *,
        ai_provider: AIProvider | None = None,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:
        self.db = db
        self.ai_provider = ai_provider or create_ai_provider()

        self.run_repository = RunRepository(db)
        self.document_service = DocumentService(db)
        self.retrieval_service = RetrievalService(db, embedding_provider)
        self.evidence_service = EvidenceService(db)
        self.conflict_service = ConflictService(db)
        self.finding_service = FindingService(db)
        self.commit_service = CommitService(db)

    # ------------------------------------------------------------------
    # Run a document version through the full pipeline up to findings
    # ------------------------------------------------------------------

    def run(
        self,
        *,
        document_id: UUID,
        document_version_id: UUID,
        case_id: str,
    ) -> dict:
        document_service = self.document_service

        # This raises AppError(DOCUMENT_NOT_FOUND / VERSION_NOT_FOUND) if
        # either does not exist -- fail fast, before creating a Run row.
        version = document_service.get_version(
            document_id, document_version_id
        )

        run_id = str(uuid4())

        with transaction(self.db):
            self.run_repository.create(
                run_id=run_id,
                case_id=case_id,
                document_id=str(document_id),
                document_version_id=str(document_version_id),
                status="running",
            )

        parsed = document_service.parse_version(
            document_id=document_id,
            version_id=document_version_id,
        )

        with transaction(self.db):
            self.retrieval_service.chunk_and_embed_version(
                document_id=document_id,
                document_version_id=document_version_id,
                parsed_document=parsed,
            )

        # --- Extraction, via the durable, checkpointed LangGraph workflow.
        with create_checkpointer() as checkpointer:
            checkpointer.setup()
            workflow = build_workflow(checkpointer)

            config = {"configurable": {"thread_id": run_id}}

            graph_result = workflow.invoke(
                _initial_agent_state(
                    run_id=run_id,
                    document_id=str(document_id),
                    document_version_id=str(document_version_id),
                    parsed_content=parsed.text,
                ),
                config=config,
            )

        facts = graph_result.get("extracted_facts", [])
        usage = graph_result.get("usage", {})

        with transaction(self.db):
            self.run_repository.record_usage(
                run_id,
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
                estimated_cost=usage.get("estimated_cost", 0.0),
            )

        if graph_result.get("status") == "failed":
            with transaction(self.db):
                self.run_repository.set_status(run_id, "failed")

            return {
                "run_id": run_id,
                "case_id": case_id,
                "status": "failed",
                "errors": graph_result.get("errors", []),
                "facts": [],
                "conflicts": [],
                "findings": [],
            }

        # --- Persist evidence, resolving each quote to its source chunk.
        with transaction(self.db):
            persisted_evidence = self.evidence_service.persist_facts_evidence(
                run_id=run_id,
                document_id=document_id,
                document_version_id=document_version_id,
                facts=facts,
            )

            evidence_by_field: dict[str, list[UUID]] = {}

            for row in persisted_evidence:
                evidence_by_field.setdefault(row.field, []).append(row.id)

                if row.chunk_id is None and row.quote:
                    best = self.retrieval_service.find_best_chunk_for_quote(
                        quote=row.quote,
                        document_version_id=document_version_id,
                    )

                    if best is not None:
                        row.chunk_id = str(best.chunk_id)

                        # Page-aware evidence references: the matched
                        # chunk's real page_index (from the parser --
                        # PDF/DOCX page structure, or the OCR'd page
                        # number) is authoritative. It overrides
                        # whatever location the extraction step
                        # self-reported (which for a real LLM provider
                        # is a best guess, and for the deterministic
                        # provider is only a line number, not a page).
                        if best.page_index is not None:
                            row.location = f"page {best.page_index + 1}"

        # --- Conflict detection against the committed register.
        with transaction(self.db):
            conflicts = self.conflict_service.detect(
                run_id=run_id,
                case_id=case_id,
                document_version_id=document_version_id,
                facts=facts,
                evidence_by_field=evidence_by_field,
            )

        # --- Deterministic rule validation.
        violations = run_rules(facts)

        # --- Findings: conflicts, routine new facts, and rule violations.
        with transaction(self.db):
            conflicted_fields = {c.field for c in conflicts}
            unchanged_fields = self.conflict_service.unchanged_fields(
                case_id=case_id,
                facts=facts,
            )

            findings = []
            findings += self.finding_service.generate_from_conflicts(
                run_id=run_id,
                case_id=case_id,
                conflicts=conflicts,
            )
            findings += self.finding_service.generate_from_facts(
                run_id=run_id,
                case_id=case_id,
                facts=facts,
                evidence_by_field=evidence_by_field,
                conflicted_fields=conflicted_fields | unchanged_fields,
            )
            findings += self.finding_service.generate_from_rule_violations(
                run_id=run_id,
                case_id=case_id,
                violations=violations,
                evidence_by_field=evidence_by_field,
            )

        with transaction(self.db):
            self.run_repository.set_status(run_id, "pending_review")

        return {
            "run_id": run_id,
            "case_id": case_id,
            "status": "pending_review",
            "facts": facts,
            "conflicts": [str(c.id) for c in conflicts],
            "findings": [str(f.id) for f in findings],
        }

    # ------------------------------------------------------------------
    # Incremental update: a new version of an already-processed case
    # ------------------------------------------------------------------

    def run_incremental_update(
        self,
        *,
        document_id: UUID,
        document_version_id: UUID,
        case_id: str,
    ) -> dict:
        """Process a newly-arrived document version (T090-T092).

        This reuses `run()` unchanged: chunking/embedding is scoped to
        the new version only (previous versions' chunks are untouched),
        conflict detection compares only the new version's facts
        against the currently committed register, and commit only ever
        rewrites the specific (case_id, field) pairs that were
        approved this run -- every other field in the register is left
        byte-identical.
        """

        return self.run(
            document_id=document_id,
            document_version_id=document_version_id,
            case_id=case_id,
        )

    # ------------------------------------------------------------------
    # Finalize review: commit approved findings, resume the graph
    # ------------------------------------------------------------------

    def finalize_review(self, run_id: str) -> dict:
        run = self.run_repository.get(run_id)

        if run is None:
            raise AppError(
                code="RUN_NOT_FOUND",
                message="Run not found",
                status_code=404,
            )

        with transaction(self.db):
            commit_result = self.commit_service.commit_run(run_id)

        final_status = (
            "completed" if not commit_result["still_pending"] else "pending_review"
        )

        with transaction(self.db):
            self.run_repository.set_status(run_id, final_status)

        # Resume the durable graph so its own checkpointed state also
        # reflects the outcome (proves T072: pause -> persist -> resume).
        review_status = "approved" if commit_result["committed"] else "rejected"

        with create_checkpointer() as checkpointer:
            checkpointer.setup()
            workflow = build_workflow(checkpointer)

            config = {"configurable": {"thread_id": run_id}}

            if workflow.get_state(config).values:
                workflow.update_state(config, {"review_status": review_status})
                workflow.invoke(None, config=config)

        return {
            "run_id": run_id,
            "status": final_status,
            **commit_result,
        }

    def get_run(self, run_id: str) -> dict:
        run = self.run_repository.get(run_id)

        if run is None:
            raise AppError(
                code="RUN_NOT_FOUND",
                message="Run not found",
                status_code=404,
            )

        return {
            "run_id": run.id,
            "case_id": run.case_id,
            "document_id": run.document_id,
            "document_version_id": run.document_version_id,
            "status": run.status,
            "created_at": run.created_at,
            "updated_at": run.updated_at,
            "input_tokens": run.input_tokens,
            "output_tokens": run.output_tokens,
            "estimated_cost": run.estimated_cost,
        }
