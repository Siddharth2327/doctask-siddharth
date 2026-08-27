from abc import ABC, abstractmethod

from app.integrations.ai.models import AIRequest, AIResponse


class AIProvider(ABC):
    """Provider-neutral interface for external AI model providers."""

    @abstractmethod
    def generate(self, request: AIRequest) -> AIResponse:
        """Generate a response from the configured AI provider."""
        raise NotImplementedError