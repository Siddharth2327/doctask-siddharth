import json
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.repositories.finding import FindingRepository
from app.rules.engine import RuleViolation


class FindingService:
    """Application service for generating findings (T063).

    Every finding is one independently reviewable unit. Three kinds
    are produced from a run:

    - "conflict"   -- a newly extracted value contradicts the
                      currently committed register value.
    - "extraction" -- a newly extracted value with no prior committed
                      value for that field (routine, still requires
                      approval before it can be committed).
    - "rule_violation" -- a deterministic rule failed (missing field,
                      missing evidence, invalid date/amount).

    A field that has a conflict finding does not also get a duplicate
    "extraction" finding for the same run -- the conflict finding IS
    the reviewable decision for that field's new value.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = FindingRepository(db)

    def generate_from_conflicts(
        self,
        *,
        run_id: str,
        case_id: str,
        conflicts: list,
    ) -> list:
        findings = []

        for conflict in conflicts:
            evidence_ids = [
                e
                for e in (conflict.new_evidence_id, conflict.existing_evidence_id)
                if e is not None
            ]

            findings.append(
                self.repository.create(
                    finding_id=uuid4(),
                    run_id=run_id,
                    case_id=case_id,
                    type="conflict",
                    field=conflict.field,
                    proposed_value=conflict.new_value,
                    severity="high",
                    confidence=None,
                    evidence_ids=evidence_ids,
                    rationale=(
                        f"New value '{conflict.new_value}' for "
                        f"'{conflict.field}' conflicts with the currently "
                        f"committed value '{conflict.existing_value}'."
                    ),
                    conflict_id=conflict.id,
                )
            )

        return findings

    def generate_from_facts(
        self,
        *,
        run_id: str,
        case_id: str,
        facts: list[dict[str, Any]],
        evidence_by_field: dict[str, list[UUID]],
        conflicted_fields: set[str],
    ) -> list:
        findings = []

        for fact in facts:
            field = fact.get("field")

            if not field or field in conflicted_fields:
                continue

            findings.append(
                self.repository.create(
                    finding_id=uuid4(),
                    run_id=run_id,
                    case_id=case_id,
                    type="extraction",
                    field=field,
                    proposed_value=str(fact.get("value")),
                    severity="low",
                    confidence=fact.get("confidence"),
                    evidence_ids=evidence_by_field.get(field, []),
                    rationale=f"New value extracted for '{field}'.",
                )
            )

        return findings

    def generate_from_rule_violations(
        self,
        *,
        run_id: str,
        case_id: str,
        violations: list[RuleViolation],
        evidence_by_field: dict[str, list[UUID]],
    ) -> list:
        findings = []

        for violation in violations:
            findings.append(
                self.repository.create(
                    finding_id=uuid4(),
                    run_id=run_id,
                    case_id=case_id,
                    type="rule_violation",
                    field=violation.field,
                    proposed_value=None,
                    severity=violation.severity,
                    confidence=None,
                    evidence_ids=evidence_by_field.get(violation.field, [])
                    if violation.field
                    else [],
                    rationale=violation.message,
                )
            )

        return findings

    def list_for_run(self, run_id: str, status: str | None = None):
        return self.repository.list_for_run(run_id, status=status)

    def list_for_case(self, case_id: str, status: str | None = None):
        return self.repository.list_for_case(case_id, status=status)

    def get(self, finding_id: str):
        return self.repository.get(finding_id)

    @staticmethod
    def evidence_ids_of(finding) -> list[str]:
        return json.loads(finding.evidence_ids)
