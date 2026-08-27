import json

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

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


class GeminiProvider(AIProvider):
    """Real AI provider backed by the Google Gemini API."""

    def __init__(self, api_key: str | None = None) -> None:
        self.client = genai.Client(api_key=api_key or settings.ai_api_key)

    def generate(self, request: AIRequest) -> AIResponse:
        system_messages = [
            m["content"] for m in request.messages if m["role"] == "system"
        ]
        other_messages = [
            m["content"] for m in request.messages if m["role"] != "system"
        ]

        config = types.GenerateContentConfig(
            system_instruction="\n\n".join(system_messages) or None,
            temperature=request.temperature,
            response_mime_type="application/json",
            response_json_schema=request.response_schema,
            http_options=types.HttpOptions(
                timeout=int(request.timeout * 1000)
            ),
        )

        try:
            response = self.client.models.generate_content(
                model=request.model,
                contents="\n\n".join(other_messages),
                config=config,
            )
        except genai_errors.ClientError as exc:
            status = getattr(exc, "code", None)

            if status == 401 or status == 403:
                raise AIAuthenticationError(str(exc)) from exc
            if status == 429:
                raise AIRateLimitError(str(exc)) from exc

            raise AIInvalidRequestError(str(exc)) from exc
        except genai_errors.ServerError as exc:
            raise AIUnavailableError(str(exc)) from exc
        except TimeoutError as exc:
            raise AITimeoutError(str(exc)) from exc

        try:
            content = json.loads(response.text)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise AIStructuredOutputError(
                f"Gemini response was not valid JSON: {exc}"
            ) from exc

        usage_metadata = response.usage_metadata

        return AIResponse(
            content=content,
            model=request.model,
            usage=AIUsage(
                input_tokens=(
                    usage_metadata.prompt_token_count if usage_metadata else 0
                ) or 0,
                output_tokens=(
                    usage_metadata.candidates_token_count
                    if usage_metadata
                    else 0
                )
                or 0,
            ),
        )
