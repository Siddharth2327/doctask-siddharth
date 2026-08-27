from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.repositories.canonical_fact import CanonicalFactRepository
from app.repositories.conflict import ConflictRepository


def _values_conflict(existing: str, new: str) -> bool:
    """Best-effort normalized comparison.

    Numeric-looking values are compared as numbers (so "100000" and
    "100,000.00" are NOT treated as a conflict); everything else is
    compared as case/whitespace-insensitive text.
    """

    def as_number(value: str) -> float | None:
        cleaned = value.replace(",", "").replace("$", "").strip()

        try:
            return float(cleaned)
        except ValueError:
            return None

    existing_number = as_number(existing)
    new_number = as_number(new)

    if existing_number is not None and new_number is not None:
        return existing_number != new_number

    return existing.strip().lower() != new.strip().lower()


class ConflictService:
    """Application service for detecting contradictions (T060).

    A conflict is raised whenever a newly extracted fact disagrees
    with the value currently committed in the CanonicalFact register
    for the same (case_id, field). The existing value is never
    silently overwritten -- both sides are persisted with their
    respective evidence, and resolution only happens through the
    normal finding -> human review -> commit path.
    """

    def __init__(self, db: Session) -> None:
        self.db = db
        self.canonical_repository = CanonicalFactRepository(db)
        self.conflict_repository = ConflictRepository(db)

    def detect(
        self,
        *,
        run_id: str,
        case_id: str,
        document_version_id: UUID,
        facts: list[dict[str, Any]],
        evidence_by_field: dict[str, list[UUID]],
    ) -> list:
        conflicts = []

        for fact in facts:
            field = fact.get("field")
            new_value = fact.get("value")

            if not field or new_value is None:
                continue

            existing = self.canonical_repository.get_by_field(case_id, field)

            if existing is None:
                continue

            if not _values_conflict(existing.value, str(new_value)):
                continue

            new_evidence_ids = evidence_by_field.get(field, [])

            conflicts.append(
                self.conflict_repository.create(
                    conflict_id=uuid4(),
                    run_id=run_id,
                    case_id=case_id,
                    field=field,
                    existing_value=existing.value,
                    existing_evidence_id=existing.evidence_id,
                    new_value=str(new_value),
                    new_evidence_id=(
                        new_evidence_ids[0] if new_evidence_ids else None
                    ),
                    document_version_id=document_version_id,
                )
            )

        return conflicts

    def unchanged_fields(
        self,
        *,
        case_id: str,
        facts: list[dict[str, Any]],
    ) -> set[str]:
        """Fields whose newly extracted value exactly matches what is
        already committed -- no new information, nothing to review.

        Used to keep incremental updates focused (T090-T092): re-running
        a case should not spam reviewers with findings that just
        restate the already-committed value.
        """

        unchanged = set()

        for fact in facts:
            field = fact.get("field")
            value = fact.get("value")

            if not field or value is None:
                continue

            existing = self.canonical_repository.get_by_field(case_id, field)

            if existing is not None and not _values_conflict(
                existing.value, str(value)
            ):
                unchanged.add(field)

        return unchanged
