from hashlib import sha256
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.transaction import transaction
from app.integrations.storage.provider import get_storage
from app.parsing import ParsedDocument, get_parser
from app.repositories.document import DocumentRepository


class DocumentService:
    """Application service for document operations."""

    def __init__(self, db: Session) -> None:
        self.repository = DocumentRepository(db)
        self.storage = get_storage()

    def list_documents(self):
        return self.repository.list_all()

    def upload_document(
        self,
        *,
        name: str,
        filename: str,
        content_type: str,
        source: str,
        content: bytes,
    ):
        name = name.strip()
        source = source.strip()
        filename = filename.strip()

        if not name:
            raise AppError(
                code="INVALID_DOCUMENT_NAME",
                message="Document name is required",
                status_code=400,
            )

        if len(name) > 255:
            raise AppError(
                code="INVALID_DOCUMENT_NAME",
                message="Document name must not exceed 255 characters",
                status_code=400,
            )

        if not source:
            raise AppError(
                code="INVALID_DOCUMENT_SOURCE",
                message="Document source is required",
                status_code=400,
            )

        if len(source) > 255:
            raise AppError(
                code="INVALID_DOCUMENT_SOURCE",
                message="Document source must not exceed 255 characters",
                status_code=400,
            )

        if not filename:
            raise AppError(
                code="INVALID_FILENAME",
                message="Filename is required",
                status_code=400,
            )

        if len(filename) > 255:
            raise AppError(
                code="INVALID_FILENAME",
                message="Filename must not exceed 255 characters",
                status_code=400,
            )

        if not content:
            raise AppError(
                code="EMPTY_DOCUMENT",
                message="Uploaded document is empty",
                status_code=400,
            )

        content_hash = sha256(content).hexdigest()

        document_id = uuid4()
        version_id = uuid4()

        storage_reference = (
            f"documents/{document_id}/"
            f"versions/{version_id}/{filename}"
        )

        self.storage.store(
            reference=storage_reference,
            content=content,
        )

        try:
            with transaction(self.repository.db):
                document = self.repository.create_document(
                    document_id=document_id,
                    name=name,
                    source=source,
                )

                version = self.repository.create_version(
                    version_id=version_id,
                    document_id=document.id,
                    version_number=1,
                    parent_version_id=None,
                    filename=filename,
                    content_type=content_type,
                    content_hash=content_hash,
                    source=source,
                    storage_reference=storage_reference,
                )
            return document, version

        except Exception:
            self.storage.delete(reference=storage_reference)
            raise
    
    def upload_new_version(
        self,
        *,
        document_id: UUID,
        filename: str,
        content_type: str,
        source: str,
        content: bytes,
    ):
        filename = filename.strip()

        if not filename:
            raise AppError(
                code="INVALID_FILENAME",
                message="Filename is required",
                status_code=400,
            )

        if len(filename) > 255:
            raise AppError(
                code="INVALID_FILENAME",
                message="Filename must not exceed 255 characters",
                status_code=400,
            )

        if not content:
            raise AppError(
                code="EMPTY_DOCUMENT",
                message="Uploaded document is empty",
                status_code=400,
            )

        content_hash = sha256(content).hexdigest()

        with transaction(self.repository.db):
            document = self.repository.get(str(document_id))

            if document is None:
                raise AppError(
                    code="DOCUMENT_NOT_FOUND",
                    message="Document not found",
                    status_code=404,
                )

            duplicate = self.repository.find_by_content_hash(
                document_id=document_id,
                content_hash=content_hash,
            )

            if duplicate is not None:
                return document, duplicate, True

            latest = self.repository.get_latest_version(
                document_id,
            )

            version_number = (
                latest.version_number + 1
                if latest is not None
                else 1
            )

            parent_version_id = (
                latest.id
                if latest is not None
                else None
            )

            version_id = uuid4()

            storage_reference = (
                f"documents/{document_id}/"
                f"versions/{version_id}/{filename}"
            )

            self.storage.store(
                reference=storage_reference,
                content=content,
            )

            try:
                version = self.repository.create_version(
                    version_id=version_id,
                    document_id=document_id,
                    version_number=version_number,
                    parent_version_id=parent_version_id,
                    filename=filename,
                    content_type=content_type,
                    content_hash=content_hash,
                    source=source,
                    storage_reference=storage_reference,
                )

            except Exception:
                self.storage.delete(
                    reference=storage_reference,
                )
                raise

        return document, version, False

    def get_versions(
        self,
        document_id: UUID,
    ):
        document = self.repository.get(str(document_id))

        if document is None:
            raise AppError(
                code="DOCUMENT_NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        return self.repository.get_versions(document_id)

    def get_version(
        self,
        document_id: UUID,
        version_id: UUID,
    ):
        document = self.repository.get(str(document_id))

        if document is None:
            raise AppError(
                code="DOCUMENT_NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        version = self.repository.get_version(
            document_id,
            version_id,
        )

        if version is None:
            raise AppError(
                code="VERSION_NOT_FOUND",
                message="Document version not found",
                status_code=404,
            )

        return version
    
    def parse_version(
        self,
        *,
        document_id: UUID,
        version_id: UUID,
    ) -> ParsedDocument:
        """Retrieve and parse a specific document version."""

        document = self.repository.get(str(document_id))

        if document is None:
            raise AppError(
                code="DOCUMENT_NOT_FOUND",
                message="Document not found",
                status_code=404,
            )

        version = self.repository.get_version(
            document_id,
            version_id,
        )

        if version is None:
            raise AppError(
                code="VERSION_NOT_FOUND",
                message="Document version not found",
                status_code=404,
            )

        if not version.storage_reference:
            raise AppError(
                code="STORAGE_REFERENCE_MISSING",
                message="Document version has no storage reference",
                status_code=500,
            )

        try:
            content = self.storage.retrieve(
                reference=version.storage_reference,
            )
        except FileNotFoundError as exc:
            raise AppError(
                code="STORAGE_ERROR",
                message="Document version content is unavailable",
                status_code=500,
            ) from exc

        parser = get_parser(
            content_type=version.content_type,
            filename=version.filename,
        )

        return parser.parse(
            content=content,
            filename=version.filename,
            content_type=version.content_type,
        )