class EmbeddingProviderError(Exception):
    """Base error for all embedding provider failures."""


class EmbeddingUnknownProviderError(EmbeddingProviderError):
    """Requested embedding provider is not configured or supported."""
