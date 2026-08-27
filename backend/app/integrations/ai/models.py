from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AIUsage:
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass(frozen=True)
class AIRequest:
    messages: list[dict[str, str]]
    model: str
    temperature: float = 0.0
    timeout: float = 30.0
    response_schema: dict[str, Any] | None = None


@dataclass(frozen=True)
class AIResponse:
    content: Any
    model: str
    usage: AIUsage = field(default_factory=AIUsage)