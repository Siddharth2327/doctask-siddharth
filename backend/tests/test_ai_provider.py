import pytest

from app.core.config import settings
from app.integrations.ai.errors import (
    AITimeoutError,
    AIUnknownProviderError,
)
from app.integrations.ai.factory import create_ai_provider
from app.integrations.ai.mock import MockAIProvider
from app.integrations.ai.models import AIRequest


def make_request(**overrides) -> AIRequest:
    values = {
        "messages": [
            {
                "role": "user",
                "content": "Extract the relevant facts.",
            }
        ],
        "model": "test-model",
        "temperature": 0.0,
        "timeout": 10.0,
    }

    values.update(overrides)
    return AIRequest(**values)


def test_mock_provider_returns_response():
    provider = MockAIProvider(
        response={"competitor": "Acme"},
        input_tokens=12,
        output_tokens=8,
    )

    response = provider.generate(make_request())

    assert response.content == {"competitor": "Acme"}
    assert response.model == "test-model"
    assert response.usage.input_tokens == 12
    assert response.usage.output_tokens == 8
    assert response.usage.total_tokens == 20


def test_usage_is_captured():
    provider = MockAIProvider(
        input_tokens=100,
        output_tokens=50,
    )

    response = provider.generate(make_request())

    assert response.usage.input_tokens == 100
    assert response.usage.output_tokens == 50
    assert response.usage.total_tokens == 150


def test_timeout_is_normalized():
    provider = MockAIProvider(should_timeout=True)

    with pytest.raises(AITimeoutError):
        provider.generate(make_request(timeout=5.0))


def test_request_preserves_structured_output_schema():
    schema = {
        "type": "object",
        "properties": {
            "reason": {"type": "string"},
        },
        "required": ["reason"],
    }

    provider = MockAIProvider(response={"reason": "pricing"})

    request = make_request(response_schema=schema)
    response = provider.generate(request)

    assert provider.requests[-1].response_schema == schema
    assert response.content == {"reason": "pricing"}


def test_factory_rejects_empty_provider(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "")

    with pytest.raises(AIUnknownProviderError):
        create_ai_provider()


def test_factory_creates_mock_provider(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "mock")

    provider = create_ai_provider()

    assert isinstance(provider, MockAIProvider)


def test_factory_rejects_unknown_provider(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "unknown-provider")

    with pytest.raises(AIUnknownProviderError):
        create_ai_provider()