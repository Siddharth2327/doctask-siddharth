"""Re-embed every existing chunk with the currently configured
embedding provider.

Needed after changing EMBEDDING_PROVIDER and/or EMBEDDING_DIMENSIONS
in a deployment that already has chunks (see the docstring in
alembic/versions/c4a8f0e1d6b2_alter_chunk_embedding_dimensions.py).

Usage:
    python scripts/reembed_chunks.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal  # noqa: E402
from app.integrations.embeddings.factory import create_embedding_provider  # noqa: E402
from app.models.chunk import Chunk  # noqa: E402


def main() -> None:
    db = SessionLocal()
    provider = create_embedding_provider()

    try:
        chunks = db.query(Chunk).order_by(Chunk.id).all()

        print(f"Re-embedding {len(chunks)} chunks with {type(provider).__name__} "
              f"(dimensions={provider.dimensions})...")

        batch_size = 100

        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            embeddings = provider.embed([chunk.text for chunk in batch])

            for chunk, embedding in zip(batch, embeddings):
                chunk.embedding = embedding

            db.commit()
            print(f"  {min(start + batch_size, len(chunks))}/{len(chunks)}")

        print("Done.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
