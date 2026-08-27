import pytest

from app.core.errors import AppError  # noqa: F401  (not used directly, kept for parity with other test files' import style if needed)
from app.integrations.ai.errors import AIUnknownProviderError
from app.integrations.ai.factory import create_ai_provider
from app.integrations.ai.mock import MockAIProvider
from app.integrations.ai.deterministic import DeterministicKeyValueAIProvider


def test_empty_ai_provider_raises_instead_of_silently_using_mock(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "ai_provider", "")

    with pytest.raises(AIUnknownProviderError):
        create_ai_provider()


def test_explicit_mock_provider_still_works(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "ai_provider", "mock")

    provider = create_ai_provider()

    assert isinstance(provider, MockAIProvider)


def test_deterministic_provider_extracts_real_fields_from_the_reported_document():
    """Regression test for the exact bug reported: a clean contract with
    vendor/contract_value/dates/status must extract all five fields and
    produce zero rule violations when a real (non-mock) provider is used."""

    from app.agents.extraction import StructuredExtractionService
    from app.rules.engine import run_rules

    content = (
        "MASTER SERVICES AGREEMENT\n\n"
        "Vendor: Acme Supplies\n"
        "Contract Value: 100000\n"
        "Start Date: 2026-01-01\n"
        "End Date: 2026-12-31\n"
        "Status: Active"
    )

    provider = DeterministicKeyValueAIProvider()
    service = StructuredExtractionService(provider)

    result, _, _ = service.extract(
        document_id="af2e8d90-7ba1-4701-9daa-4c5d7b578a55",
        document_version_id="1cca43bb-a259-4cf0-919b-f3ee6f6becb0",
        content=content,
        model="deterministic-v1",
    )

    fields = {fact.field: fact.value for fact in result.facts}

    assert fields["vendor"] == "Acme Supplies"
    assert fields["contract_value"] == "100000"
    assert fields["start_date"] == "2026-01-01"
    assert fields["end_date"] == "2026-12-31"
    assert fields["status"] == "Active"

    violations = run_rules([fact.model_dump() for fact in result.facts])

    assert violations == []


def test_mock_provider_default_response_produces_zero_facts_not_an_error():
    """Documents the mock provider's actual contract: it's a safe,
    non-crashing stub for AI-provider-behavior tests (retries, timeouts,
    error mapping) -- NOT a content-aware extractor. Zero facts is its
    correct, expected behavior; the fix is that 'mock' can no longer be
    reached silently by an unconfigured AI_PROVIDER (see the test above)."""

    from app.agents.extraction import StructuredExtractionService

    provider = MockAIProvider()
    service = StructuredExtractionService(provider)

    result, _, _ = service.extract(
        document_id="doc-1",
        document_version_id="v-1",
        content="Vendor: Acme Supplies\nContract Value: 100000",
        model="mock-model",
    )

    assert result.facts == []