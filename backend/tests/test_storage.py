from pathlib import Path

import pytest

from app.integrations.storage.local import LocalStorageAdapter


def test_local_storage_store_retrieve_exists_delete(tmp_path: Path):
    storage = LocalStorageAdapter(tmp_path)

    reference = "documents/test.txt"
    content = b"Docsnary storage test"

    assert storage.exists(reference=reference) is False

    stored_reference = storage.store(
        reference=reference,
        content=content,
    )

    assert stored_reference == reference
    assert storage.exists(reference=reference) is True
    assert storage.retrieve(reference=reference) == content

    storage.delete(reference=reference)

    assert storage.exists(reference=reference) is False


def test_local_storage_prevents_path_escape(tmp_path: Path):
    storage = LocalStorageAdapter(tmp_path)

    with pytest.raises(ValueError):
        storage.store(
            reference="../outside.txt",
            content=b"should not escape",
        )