from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):
    """Provider-neutral interface for text embedding generation."""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per input text, same order."""
        raise NotImplementedError

    @property
    @abstractmethod
    def dimensions(self) -> int:
        raise NotImplementedError
