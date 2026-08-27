from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

RULESET_VERSION = "v1"

REQUIRED_FIELDS = ("vendor", "contract_value")
DATE_FIELDS_SUFFIX = "_date"
AMOUNT_FIELDS = ("contract_value", "invoice_amount")

_DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y", "%B %d, %Y", "%b %d, %Y")


@dataclass(frozen=True)
class RuleViolation:
    rule_name: str
    field: str | None
    message: str
    severity: str  # low | medium | high


def _parse_amount(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        cleaned = re.sub(r"[^0-9.\-]", "", value)

        if not cleaned:
            return None

        try:
            return float(cleaned)
        except ValueError:
            return None

    return None


def _parse_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value

    if not isinstance(value, str):
        return None

    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue

    return None


def check_required_fields(
    facts_by_field: dict[str, Any],
) -> list[RuleViolation]:
    violations = []

    for field in REQUIRED_FIELDS:
        if field not in facts_by_field:
            violations.append(
                RuleViolation(
                    rule_name="required_field_present",
                    field=field,
                    message=f"Required field '{field}' was not extracted.",
                    severity="high",
                )
            )

    return violations


def check_evidence_present(
    facts: list[dict[str, Any]],
) -> list[RuleViolation]:
    violations = []

    for fact in facts:
        if not fact.get("evidence"):
            violations.append(
                RuleViolation(
                    rule_name="evidence_required",
                    field=fact.get("field"),
                    message=(
                        f"Field '{fact.get('field')}' has no supporting "
                        "evidence and cannot be trusted."
                    ),
                    severity="high",
                )
            )

    return violations


def check_dates(
    facts: list[dict[str, Any]],
) -> list[RuleViolation]:
    violations = []

    for fact in facts:
        field = fact.get("field") or ""

        if not field.endswith(DATE_FIELDS_SUFFIX):
            continue

        if _parse_date(fact.get("value")) is None:
            violations.append(
                RuleViolation(
                    rule_name="valid_date",
                    field=field,
                    message=(
                        f"Field '{field}' value "
                        f"'{fact.get('value')}' is not a valid date."
                    ),
                    severity="medium",
                )
            )

    return violations


def check_amounts(
    facts: list[dict[str, Any]],
) -> list[RuleViolation]:
    violations = []

    for fact in facts:
        field = fact.get("field")

        if field not in AMOUNT_FIELDS:
            continue

        amount = _parse_amount(fact.get("value"))

        if amount is None or amount <= 0:
            violations.append(
                RuleViolation(
                    rule_name="valid_amount",
                    field=field,
                    message=(
                        f"Field '{field}' value "
                        f"'{fact.get('value')}' is not a valid positive amount."
                    ),
                    severity="medium",
                )
            )

    return violations


def run_rules(facts: list[dict[str, Any]]) -> list[RuleViolation]:
    """Run all deterministic rules against a run's extracted facts.

    Deliberately code, not an LLM call (T061: "Do not use an LLM for
    something that can simply be validated in code"). Returns an empty
    list when the corpus is clean -- the zero-findings case is a real,
    supported outcome, not an edge case to special-case away.
    """

    facts_by_field = {
        fact.get("field"): fact.get("value")
        for fact in facts
        if fact.get("field")
    }

    violations: list[RuleViolation] = []
    violations += check_required_fields(facts_by_field)
    violations += check_evidence_present(facts)
    violations += check_dates(facts)
    violations += check_amounts(facts)

    return violations
