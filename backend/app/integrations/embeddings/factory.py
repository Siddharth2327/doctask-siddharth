from app.core.config import settings
from app.integrations.embeddings.base import EmbeddingProvider
from app.integrations.embeddings.errors import EmbeddingUnknownProviderError
from app.integrations.embeddings.mock import DeterministicEmbeddingProvider
from app.models.chunk import EMBEDDING_DIMENSIONS


def create_embedding_provider() -> EmbeddingProvider:
    provider = settings.embedding_provider.strip().lower()

    if provider in {"", "mock", "deterministic"}:
        return DeterministicEmbeddingProvider(EMBEDDING_DIMENSIONS)

    if provider == "openai":
        from app.integrations.embeddings.openai_embeddings import (
            OpenAIEmbeddingProvider,
        )

        return OpenAIEmbeddingProvider(dimensions=EMBEDDING_DIMENSIONS)

    raise EmbeddingUnknownProviderError(
        f"Unsupported embedding provider: {settings.embedding_provider}"
    )
