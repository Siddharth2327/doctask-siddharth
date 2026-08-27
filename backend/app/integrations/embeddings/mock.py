import hashlib
import math
import re

from app.integrations.embeddings.base import EmbeddingProvider

_WORD_RE = re.compile(r"[a-z0-9]+")


class DeterministicEmbeddingProvider(EmbeddingProvider):
    """A hashing-based bag-of-words embedding provider.

    This is NOT a semantic embedding model. It exists so retrieval
    (T052/T053) can be developed, tested, and demoed without a paid
    API key: texts that share vocabulary end up with smaller cosine
    distance than texts that do not, which is enough to prove the
    chunk -> embed -> pgvector -> top-k retrieval path end to end.
    Swapping in a real embedding model later only means implementing
    a new `EmbeddingProvider` and pointing the factory at it -- the
    persistence/retrieval layer is unaffected.
    """

    def __init__(self, dimensions: int = 32) -> None:
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self._dimensions

        words = _WORD_RE.findall(text.lower())

        if not words:
            return vector

        for word in words:
            digest = hashlib.sha256(word.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:4], "big") % self._dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[bucket] += sign

        norm = math.sqrt(sum(component * component for component in vector))

        if norm == 0:
            return vector

        return [component / norm for component in vector]
