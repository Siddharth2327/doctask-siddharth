import openai

from app.core.config import settings
from app.integrations.embeddings.base import EmbeddingProvider
from app.integrations.embeddings.errors import EmbeddingProviderError


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """Real embedding provider backed by the OpenAI Embeddings API.

    OpenAI's `text-embedding-3-*` models support a `dimensions`
    parameter to truncate their native output to a smaller size, which
    is what lets this provider's output size match whatever
    `settings.embedding_dimensions` the pgvector column was migrated
    to -- there is exactly one dimension setting for the whole
    application, and every configured provider (mock or real) must
    produce vectors of that size.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        dimensions: int | None = None,
    ) -> None:
        self.client = openai.OpenAI(api_key=api_key or settings.ai_api_key)
        self.model = model or settings.embedding_model
        self._dimensions = dimensions or settings.embedding_dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts,
                dimensions=self._dimensions,
            )
        except openai.OpenAIError as exc:
            raise EmbeddingProviderError(
                f"OpenAI embedding request failed: {exc}"
            ) from exc

        # The API guarantees results are returned in input order.
        return [item.embedding for item in response.data]
