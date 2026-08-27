from app.core.config import settings
from app.integrations.ai.base import AIProvider
from app.integrations.ai.errors import AIUnknownProviderError
from app.integrations.ai.mock import MockAIProvider
from app.integrations.ai.deterministic import DeterministicKeyValueAIProvider


def create_ai_provider() -> AIProvider:
    """Build the configured AI provider.

    Real providers (openai/anthropic/gemini) are imported lazily inside
    this function, not at module load time, so that installing this
    package's requirements is enough to run the app with the
    deterministic/mock providers even before the optional real-provider
    SDKs are configured with a key -- and so a missing/invalid key only
    surfaces as an error when a real provider is actually selected.
    """

    provider = settings.ai_provider.strip().lower()

    if provider == "":
        raise AIUnknownProviderError(
            "AI_PROVIDER is not set. Set it to one of: "
            "mock, deterministic, openai, anthropic, gemini. "
            "For local development without a paid API key, use "
            "'deterministic' -- 'mock' returns a fixed canned response "
            "unrelated to document content and is intended for AI-provider "
            "unit tests, not real document processing."
        )

    if provider == "mock":
        return MockAIProvider()

    if provider == "deterministic":
        return DeterministicKeyValueAIProvider()

    if provider == "openai":
        from app.integrations.ai.openai_provider import OpenAIProvider

        return OpenAIProvider()

    if provider == "anthropic":
        from app.integrations.ai.anthropic_provider import AnthropicProvider

        return AnthropicProvider()

    if provider == "gemini":
        from app.integrations.ai.gemini import GeminiProvider

        return GeminiProvider()

    raise AIUnknownProviderError(
        f"Unsupported AI provider: {settings.ai_provider}"
    )