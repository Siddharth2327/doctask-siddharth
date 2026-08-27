from fastapi.testclient import TestClient
from sqlalchemy import text

from app.db.session import engine
from app.main import app


client = TestClient(app)


def cleanup_documents() -> None:
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM document_versions"))
        connection.execute(text("DELETE FROM documents"))


def test_upload_document():
    cleanup_documents()

    response = client.post(
        "/documents",
        data={
            "name": "Test Document",
            "source": "automated-test",
        },
        files={
            "file": (
                "test.txt",
                b"This is a test document.",
                "text/plain",
            )
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["name"] == "Test Document"
    assert body["source"] == "automated-test"

    version = body["version"]

    assert version["filename"] == "test.txt"
    assert version["content_type"] == "text/plain"
    assert version["version_number"] == 1
    assert len(version["content_hash"]) == 64


def test_upload_empty_document_fails():
    cleanup_documents()

    response = client.post(
        "/documents",
        data={
            "name": "Empty Document",
            "source": "automated-test",
        },
        files={
            "file": (
                "empty.txt",
                b"",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400

    assert response.json() == {
        "error": {
            "code": "EMPTY_DOCUMENT",
            "message": "Uploaded document is empty",
        }
    }


def test_upload_without_name_fails():
    cleanup_documents()

    response = client.post(
        "/documents",
        data={
            "source": "automated-test",
        },
        files={
            "file": (
                "test.txt",
                b"content",
                "text/plain",
            )
        },
    )

    assert response.status_code == 422


def test_upload_without_source_fails():
    cleanup_documents()

    response = client.post(
        "/documents",
        data={
            "name": "Test Document",
        },
        files={
            "file": (
                "test.txt",
                b"content",
                "text/plain",
            )
        },
    )

    assert response.status_code == 422

def test_failed_upload_does_not_create_document():
    cleanup_documents()

    response = client.post(
        "/documents",
        data={
            "name": "Should Not Exist",
            "source": "automated-test",
        },
        files={
            "file": (
                "empty.txt",
                b"",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400

    with engine.connect() as connection:
        document_count = connection.execute(
            text(
                "SELECT COUNT(*) FROM documents "
                "WHERE name = 'Should Not Exist'"
            )
        ).scalar_one()

    assert document_count == 0    

def test_upload_new_version_via_api_returns_wrapped_response():
    cleanup_documents()

    upload_response = client.post(
        "/documents",
        data={"name": "Versioned Doc", "source": "automated-test"},
        files={"file": ("v1.txt", b"Vendor: Acme Supplies", "text/plain")},
    )
    document_id = upload_response.json()["id"]

    response = client.post(
        f"/documents/{document_id}/versions",
        data={"source": "automated-test"},
        files={"file": ("v2.txt", b"Vendor: Acme Supplies v2", "text/plain")},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["is_duplicate"] is False
    assert body["version"]["version_number"] == 2
    assert body["version"]["filename"] == "v2.txt"
    assert body["version"]["document_id"] == document_id
    assert body["version"]["parent_version_id"] is not None


def test_upload_duplicate_version_content_is_flagged_not_duplicated():
    cleanup_documents()

    upload_response = client.post(
        "/documents",
        data={"name": "Dup Doc", "source": "automated-test"},
        files={"file": ("v1.txt", b"Same content", "text/plain")},
    )
    document_id = upload_response.json()["id"]

    response = client.post(
        f"/documents/{document_id}/versions",
        data={"source": "automated-test"},
        files={"file": ("v1-again.txt", b"Same content", "text/plain")},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["is_duplicate"] is True
    assert body["version"]["version_number"] == 1  # reused, not incremented

    with engine.connect() as connection:
        version_count = connection.execute(
            text(
                "SELECT COUNT(*) FROM document_versions "
                "WHERE document_id = :document_id"
            ),
            {"document_id": document_id},
        ).scalar_one()

    assert version_count == 1


def test_upload_new_version_for_unknown_document_returns_404():
    import uuid

    response = client.post(
        f"/documents/{uuid.uuid4()}/versions",
        data={"source": "automated-test"},
        files={"file": ("v2.txt", b"content", "text/plain")},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DOCUMENT_NOT_FOUND"


def test_upload_empty_new_version_returns_400():
    cleanup_documents()

    upload_response = client.post(
        "/documents",
        data={"name": "Empty Version Doc", "source": "automated-test"},
        files={"file": ("v1.txt", b"content", "text/plain")},
    )
    document_id = upload_response.json()["id"]

    response = client.post(
        f"/documents/{document_id}/versions",
        data={"source": "automated-test"},
        files={"file": ("v2.txt", b"", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "EMPTY_DOCUMENT"