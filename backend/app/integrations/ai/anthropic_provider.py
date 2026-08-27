import anthropic

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

# A generic permissive schema used when the caller does not supply
# request.response_schema. Anthropic's API has no native "JSON mode",
# so structured output is obtained by forcing a single tool call and
# reading back its (schema-validated-by-the-model) input -- this is
# the standard, reliable pattern for this provider.
_FALLBACK_SCHEMA: dict = {
    "type": "object",
    "additionalProperties": True,
}

_TOOL_NAME = "return_structured_result"


class AnthropicProvider(AIProvider):
    """Real AI provider backed by the Anthropic Messages API."""

    def __init__(self, api_key: str | None = None) -> None:
        self.client = anthropic.Anthropic(
            api_key=api_key or settings.ai_api_key,
        )

    def generate(self, request: AIRequest) -> AIResponse:
        system_messages = [
            m["content"] for m in request.messages if m["role"] == "system"
        ]
        other_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in request.messages
            if m["role"] != "system"
        ]

        schema = request.response_schema or _FALLBACK_SCHEMA

        tool = {
            "name": _TOOL_NAME,
            "description": "Return the structured result for this request.",
            "input_schema": schema,
        }

        try:
            message = self.client.messages.create(
                model=request.model,
                system="\n\n".join(system_messages) if system_messages else None,
                messages=other_messages,
                tools=[tool],
                tool_choice={"type": "tool", "name": _TOOL_NAME},
                max_tokens=4096,
                temperature=request.temperature,
                timeout=request.timeout,
            )
        except anthropic.AuthenticationError as exc:
            raise AIAuthenticationError(str(exc)) from exc
        except anthropic.RateLimitError as exc:
            raise AIRateLimitError(str(exc)) from exc
        except anthropic.APITimeoutError as exc:
            raise AITimeoutError(str(exc)) from exc
        except anthropic.BadRequestError as exc:
            raise AIInvalidRequestError(str(exc)) from exc
        except anthropic.APIConnectionError as exc:
            raise AIUnavailableError(str(exc)) from exc

        tool_use_blocks = [
            block for block in message.content if block.type == "tool_use"
        ]

        if not tool_use_blocks:
            raise AIStructuredOutputError(
                "Anthropic response did not include the requested tool call."
            )

        content = tool_use_blocks[0].input

        return AIResponse(
            content=content,
            model=message.model,
            usage=AIUsage(
                input_tokens=message.usage.input_tokens,
                output_tokens=message.usage.output_tokens,
            ),
        )
