import pymupdf
from uuid import UUID
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.db.session import engine
from app.main import app
from app.parsing import (
    DocumentParser,
    DocumentParseError,
    ParsedDocument,
    ParsedPage,
    UnsupportedDocumentError,
)
from app.parsing.factory import get_parser
from app.parsing.pdf import PdfParser
from app.parsing.text import TextParser
from app.services.document import DocumentService

client = TestClient(app)

def cleanup_documents() -> None:
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM document_versions"))
        connection.execute(text("DELETE FROM documents"))

def test_parsed_page_is_immutable():
    page = ParsedPage(
        index=1,
        text="Hello",
    )

    try:
        page.text = "Changed"
    except AttributeError:
        pass
    else:
        raise AssertionError("ParsedPage should be immutable")


def test_parsed_document_contains_normalized_metadata():
    page = ParsedPage(
        index=1,
        text="Hello world",
        metadata={"source": "page"},
    )

    document = ParsedDocument(
        text="Hello world",
        filename="example.txt",
        content_type="text/plain",
        pages=(page,),
        metadata={"parser": "text"},
    )

    assert document.text == "Hello world"
    assert document.filename == "example.txt"
    assert document.content_type == "text/plain"
    assert document.pages[0].index == 1
    assert document.pages[0].text == "Hello world"
    assert document.metadata["parser"] == "text"


def test_parser_is_abstract():
    try:
        DocumentParser()
    except TypeError:
        pass
    else:
        raise AssertionError("DocumentParser should be abstract")


def test_parsing_errors_are_distinct():
    assert issubclass(
        UnsupportedDocumentError,
        Exception,
    )

    assert issubclass(
        DocumentParseError,
        Exception,
    )

    assert UnsupportedDocumentError is not DocumentParseError

def test_text_parser_supports_plain_text():
    parser = TextParser()

    assert parser.supports("text/plain", "example.txt")
    assert parser.supports("text/plain; charset=utf-8", "example.txt")


def test_text_parser_supports_txt_extension():
    parser = TextParser()

    assert parser.supports(
        "application/octet-stream",
        "example.txt",
    )


def test_text_parser_rejects_unsupported_format():
    parser = TextParser()

    assert not parser.supports(
        "application/pdf",
        "example.pdf",
    )


def test_text_parser_returns_normalized_document():
    parser = TextParser()

    content = b"Hello Docsnary.\nThis is a test document."

    result = parser.parse(
        content=content,
        filename="example.txt",
        content_type="text/plain",
    )

    assert result.text == "Hello Docsnary.\nThis is a test document."
    assert result.filename == "example.txt"
    assert result.content_type == "text/plain"

    assert len(result.pages) == 1
    assert result.pages[0].index == 0
    assert result.pages[0].text == result.text
    assert result.pages[0].metadata["source_type"] == "text"

    assert result.metadata["parser"] == "text"


def test_text_parser_rejects_invalid_utf8():
    parser = TextParser()

    invalid_content = b"\xff\xfe\xfd"

    try:
        parser.parse(
            content=invalid_content,
            filename="broken.txt",
            content_type="text/plain",
        )
    except DocumentParseError:
        pass
    else:
        raise AssertionError(
            "Invalid UTF-8 should raise DocumentParseError"
        )

# pdf testing
def create_test_pdf() -> bytes:
    document = pymupdf.open()

    page = document.new_page()
    page.insert_text(
        (72, 72),
        "Docs­nary PDF test page one.",
    )

    page = document.new_page()
    page.insert_text(
        (72, 72),
        "Docs­nary PDF test page two.",
    )

    content = document.tobytes()

    document.close()

    return content

def test_pdf_parser_supports_pdf():
    parser = PdfParser()

    assert parser.supports(
        "application/pdf",
        "example.pdf",
    )

    assert parser.supports(
        "application/pdf; charset=binary",
        "example.pdf",
    )


def test_pdf_parser_supports_pdf_extension():
    parser = PdfParser()

    assert parser.supports(
        "application/octet-stream",
        "example.pdf",
    )


def test_pdf_parser_rejects_non_pdf():
    parser = PdfParser()

    assert not parser.supports(
        "text/plain",
        "example.txt",
    )


def test_pdf_parser_extracts_pages_and_text():
    parser = PdfParser()

    content = create_test_pdf()

    result = parser.parse(
        content=content,
        filename="example.pdf",
        content_type="application/pdf",
    )

    assert result.filename == "example.pdf"
    assert result.content_type == "application/pdf"

    assert len(result.pages) == 2

    assert result.pages[0].index == 0
    assert result.pages[0].metadata["page_number"] == 1
    assert "PDF test page one." in result.pages[0].text

    assert result.pages[1].index == 1
    assert result.pages[1].metadata["page_number"] == 2
    assert "PDF test page two." in result.pages[1].text

    assert "PDF test page one." in result.text
    assert "PDF test page two." in result.text

    assert result.metadata["parser"] == "pdf"
    assert result.metadata["page_count"] == 2


def test_pdf_parser_rejects_invalid_pdf():
    parser = PdfParser()

    try:
        parser.parse(
            content=b"this is not a PDF",
            filename="broken.pdf",
            content_type="application/pdf",
        )
    except DocumentParseError:
        pass
    else:
        raise AssertionError(
            "Invalid PDF should raise DocumentParseError"
        )

def test_factory_returns_text_parser():
    parser = get_parser(
        content_type="text/plain",
        filename="example.txt",
    )

    assert isinstance(parser, TextParser)


def test_factory_returns_pdf_parser():
    parser = get_parser(
        content_type="application/pdf",
        filename="example.pdf",
    )

    assert isinstance(parser, PdfParser)


def test_factory_supports_extension_fallback():
    parser = get_parser(
        content_type="application/octet-stream",
        filename="example.pdf",
    )

    assert isinstance(parser, PdfParser)


def test_factory_rejects_unknown_format():
    try:
        get_parser(
            content_type="application/x-unknown-format",
            filename="mystery.xyz",
        )
    except UnsupportedDocumentError:
        pass
    else:
        raise AssertionError(
            "Unsupported formats should raise UnsupportedDocumentError"
        )
def test_parse_uploaded_text_version():
    cleanup_documents()

    response = client.post(
        "/documents",
        data={
            "name": "Parse Test Document",
            "source": "automated-test",
        },
        files={
            "file": (
                "parse-test.txt",
                b"First line.\nSecond line.",
                "text/plain",
            )
        },
    )

    assert response.status_code == 201

    body = response.json()

    document_id = UUID(body["id"])
    version_id = UUID(body["version"]["id"])

    from app.db.session import SessionLocal

    db = SessionLocal()

    try:
        service = DocumentService(db)

        parsed = service.parse_version(
            document_id=document_id,
            version_id=version_id,
        )

        assert isinstance(parsed, ParsedDocument)
        assert parsed.filename == "parse-test.txt"
        assert parsed.content_type == "text/plain"
        assert parsed.text == "First line.\nSecond line."

        assert len(parsed.pages) == 1
        assert parsed.pages[0].index == 0
        assert parsed.pages[0].text == parsed.text
    finally:
        db.close()
    
def test_parse_specific_document_version():
    cleanup_documents()

    first_response = client.post(
        "/documents",
        data={
            "name": "Version Parse Test",
            "source": "automated-test",
        },
        files={
            "file": (
                "v1.txt",
                b"Original content.",
                "text/plain",
            )
        },
    )

    assert first_response.status_code == 201

    first_body = first_response.json()

    document_id = UUID(first_body["id"])
    first_version_id = UUID(first_body["version"]["id"])

    second_response = client.post(
        f"/documents/{document_id}/versions",
        data={
            "source": "automated-test",
        },
        files={
            "file": (
                "v2.txt",
                b"Updated content.",
                "text/plain",
            )
        },
    )

    assert second_response.status_code == 200

    second_body = second_response.json()
    second_version_id = UUID(second_body["id"])

    from app.db.session import SessionLocal

    db = SessionLocal()

    try:
        service = DocumentService(db)

        first_parsed = service.parse_version(
            document_id=document_id,
            version_id=first_version_id,
        )

        second_parsed = service.parse_version(
            document_id=document_id,
            version_id=second_version_id,
        )

        assert first_parsed.text == "Original content."
        assert second_parsed.text == "Updated content."

        assert first_parsed.filename == "v1.txt"
        assert second_parsed.filename == "v2.txt"
    finally:
        db.close()