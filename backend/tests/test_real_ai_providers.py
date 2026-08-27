import json
from unittest.mock import MagicMock

import pytest

from app.integrations.ai.errors import AIStructuredOutputError
from app.integrations.ai.models import AIRequest
from app.integrations.ai.pricing import estimate_cost


def make_request(**overrides) -> AIRequest:
    defaults = dict(
        messages=[
            {"role": "system", "content": "You are an extractor."},
            {"role": "user", "content": "Vendor: Acme"},
        ],
        model="test-model",
        temperature=0.0,
        timeout=10.0,
        response_schema={"type": "object", "properties": {"facts": {"type": "array"}}},
    )
    defaults.update(overrides)
    return AIRequest(**defaults)


# ----------------------------------------------------------------------
# Pricing
# ----------------------------------------------------------------------

def test_estimate_cost_known_model():
    cost = estimate_cost("gpt-4o-mini", input_tokens=1000, output_tokens=1000)
    assert cost == pytest.approx(0.00015 + 0.0006)


def test_estimate_cost_unknown_model_is_free():
    assert estimate_cost("mock-model", input_tokens=1000, output_tokens=1000) == 0.0
    assert estimate_cost("deterministic-v1", input_tokens=999, output_tokens=999) == 0.0


def test_estimate_cost_prefix_match_for_dated_model_names():
    cost = estimate_cost(
        "gpt-4o-mini-2026-08-01", input_tokens=1000, output_tokens=0
    )
    assert cost == pytest.approx(0.00015)


# ----------------------------------------------------------------------
# OpenAIProvider
# ----------------------------------------------------------------------

def test_openai_provider_happy_path():
    from app.integrations.ai.openai_provider import OpenAIProvider

    provider = OpenAIProvider(api_key="test-key")
    provider.client = MagicMock()

    fake_message = MagicMock()
    fake_message.content = json.dumps({"facts": []})
    fake_choice = MagicMock()
    fake_choice.message = fake_message
    fake_completion = MagicMock()
    fake_completion.choices = [fake_choice]
    fake_completion.model = "gpt-4o-mini"
    fake_completion.usage.prompt_tokens = 42
    fake_completion.usage.completion_tokens = 7

    provider.client.chat.completions.create.return_value = fake_completion

    response = provider.generate(make_request(model="gpt-4o-mini"))

    assert response.content == {"facts": []}
    assert response.model == "gpt-4o-mini"
    assert response.usage.input_tokens == 42
    assert response.usage.output_tokens == 7

    call_kwargs = provider.client.chat.completions.create.call_args.kwargs
    assert call_kwargs["response_format"]["type"] == "json_schema"


def test_openai_provider_invalid_json_raises():
    from app.integrations.ai.openai_provider import OpenAIProvider

    provider = OpenAIProvider(api_key="test-key")
    provider.client = MagicMock()

    fake_message = MagicMock()
    fake_message.content = "not json"
    fake_choice = MagicMock()
    fake_choice.message = fake_message
    fake_completion = MagicMock()
    fake_completion.choices = [fake_choice]

    provider.client.chat.completions.create.return_value = fake_completion

    with pytest.raises(AIStructuredOutputError):
        provider.generate(make_request())


# ----------------------------------------------------------------------
# AnthropicProvider
# ----------------------------------------------------------------------

def test_anthropic_provider_happy_path():
    from app.integrations.ai.anthropic_provider import AnthropicProvider

    provider = AnthropicProvider(api_key="test-key")
    provider.client = MagicMock()

    fake_block = MagicMock()
    fake_block.type = "tool_use"
    fake_block.input = {"facts": [{"field": "vendor", "value": "Acme"}]}

    fake_message = MagicMock()
    fake_message.content = [fake_block]
    fake_message.model = "claude-sonnet-5"
    fake_message.usage.input_tokens = 55
    fake_message.usage.output_tokens = 12

    provider.client.messages.create.return_value = fake_message

    response = provider.generate(make_request(model="claude-sonnet-5"))

    assert response.content == {"facts": [{"field": "vendor", "value": "Acme"}]}
    assert response.usage.input_tokens == 55
    assert response.usage.output_tokens == 12

    call_kwargs = provider.client.messages.create.call_args.kwargs
    assert call_kwargs["tool_choice"] == {
        "type": "tool",
        "name": "return_structured_result",
    }
    assert call_kwargs["system"] == "You are an extractor."


def test_anthropic_provider_no_tool_use_raises():
    from app.integrations.ai.anthropic_provider import AnthropicProvider

    provider = AnthropicProvider(api_key="test-key")
    provider.client = MagicMock()

    fake_text_block = MagicMock()
    fake_text_block.type = "text"

    fake_message = MagicMock()
    fake_message.content = [fake_text_block]

    provider.client.messages.create.return_value = fake_message

    with pytest.raises(AIStructuredOutputError):
        provider.generate(make_request())


# ----------------------------------------------------------------------
# GeminiProvider
# ----------------------------------------------------------------------

def test_gemini_provider_happy_path():
    from app.integrations.ai.gemini import GeminiProvider

    provider = GeminiProvider(api_key="test-key")
    provider.client = MagicMock()

    fake_response = MagicMock()
    fake_response.text = json.dumps({"facts": []})
    fake_response.usage_metadata.prompt_token_count = 30
    fake_response.usage_metadata.candidates_token_count = 8

    provider.client.models.generate_content.return_value = fake_response

    response = provider.generate(make_request(model="gemini-2.5-flash"))

    assert response.content == {"facts": []}
    assert response.usage.input_tokens == 30
    assert response.usage.output_tokens == 8


def test_gemini_provider_invalid_json_raises():
    from app.integrations.ai.gemini import GeminiProvider

    provider = GeminiProvider(api_key="test-key")
    provider.client = MagicMock()

    fake_response = MagicMock()
    fake_response.text = "not json"

    provider.client.models.generate_content.return_value = fake_response

    with pytest.raises(AIStructuredOutputError):
        provider.generate(make_request())


# ----------------------------------------------------------------------
# Factory wiring (lazy import, no SDK call made)
# ----------------------------------------------------------------------

def test_factory_returns_real_providers_without_network_call(monkeypatch):
    from app.core.config import settings
    from app.integrations.ai.factory import create_ai_provider

    for provider_name, expected_type in [
        ("openai", "OpenAIProvider"),
        ("anthropic", "AnthropicProvider"),
        ("gemini", "GeminiProvider"),
    ]:
        monkeypatch.setattr(settings, "ai_provider", provider_name)
        monkeypatch.setattr(settings, "ai_api_key", "test-key")

        provider = create_ai_provider()

        assert type(provider).__name__ == expected_type
