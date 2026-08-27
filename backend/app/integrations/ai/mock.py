from typing import Any

from app.integrations.ai.base import AIProvider
from app.integrations.ai.errors import AITimeoutError
from app.integrations.ai.models import AIRequest, AIResponse, AIUsage


class MockAIProvider(AIProvider):
    """Deterministic provider used for tests and local development."""

    def __init__(
        self,
        response: Any = None,
        *,
        input_tokens: int = 10,
        output_tokens: int = 5,
        should_timeout: bool = False,
    ) -> None:
        self.response = response if response is not None else {"ok": True}
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.should_timeout = should_timeout
        self.requests: list[AIRequest] = []

    def generate(self, request: AIRequest) -> AIResponse:
        self.requests.append(request)

        if self.should_timeout:
            raise AITimeoutError(
                f"AI request timed out after {request.timeout} seconds"
            )

        return AIResponse(
            content=self.response,
            model=request.model,
            usage=AIUsage(
                input_tokens=self.input_tokens,
                output_tokens=self.output_tokens,
            ),
        )