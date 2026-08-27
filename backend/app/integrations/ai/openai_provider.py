import json

import openai

from app.core.config import settings
from app.integrations.ai.base import AIProvider
from app.integrations.ai.errors import (
    AIAuthenticationError,
    AIInvalidRequestError,
    AIRateLimitError,
    AIStructuredOutputError,
    AITimeoutError,
    AIUnavailableError,
)
from app.integrations.ai.models import AIRequest, AIResponse, AIUsage


class OpenAIProvider(AIProvider):
    """Real AI provider backed by the OpenAI Chat Completions API.

    Uses JSON-schema constrained output (`response_format`) when the
    caller supplies `request.response_schema`, falling back to plain
    JSON-object mode otherwise. SDK exceptions are mapped onto the
    project's existing AIProviderError taxonomy so callers (retry
    logic in app.agents.workflow) don't need to know which provider
    is configured.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self.client = openai.OpenAI(
            api_key=api_key or settings.ai_api_key,
        )

    def generate(self, request: AIRequest) -> AIResponse:
        response_format: dict = {"type": "json_object"}

        if request.response_schema is not None:
            response_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": "extraction_result",
                    "schema": request.response_schema,
                    "strict": False,
                },
            }

        try:
            completion = self.client.chat.completions.create(
                model=request.model,
                messages=request.messages,
                temperature=request.temperature,
                response_format=response_format,
                timeout=request.timeout,
            )
        except openai.AuthenticationError as exc:
            raise AIAuthenticationError(str(exc)) from exc
        except openai.RateLimitError as exc:
            raise AIRateLimitError(str(exc)) from exc
        except openai.APITimeoutError as exc:
            raise AITimeoutError(str(exc)) from exc
        except openai.BadRequestError as exc:
            raise AIInvalidRequestError(str(exc)) from exc
        except openai.APIConnectionError as exc:
            raise AIUnavailableError(str(exc)) from exc

        message = completion.choices[0].message.content

        try:
            content = json.loads(message)
        except (TypeError, json.JSONDecodeError) as exc:
            raise AIStructuredOutputError(
                f"OpenAI response was not valid JSON: {exc}"
            ) from exc

        usage = completion.usage

        return AIResponse(
            content=content,
            model=completion.model,
            usage=AIUsage(
                input_tokens=usage.prompt_tokens if usage else 0,
                output_tokens=usage.completion_tokens if usage else 0,
            ),
        )
