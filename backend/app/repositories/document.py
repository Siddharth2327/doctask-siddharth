from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentVersion
from app.repositories.base import Repository


class DocumentRepository(Repository[Document]):
    """Repository for document persistence operations."""

    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get(self, entity_id: str) -> Document | None:
        return self.db.get(Document, UUID(entity_id))

    def list_all(self) -> list[Document]:
        statement = select(Document).order_by(Document.name.asc())

        return list(self.db.scalars(statement).all())

    def create_document(
        self,
        *,
        document_id: UUID,
        name: str,
        source: str,
    ) -> Document:
        document = Document(
            id=document_id,
            name=name,
            source=source,
        )

        self.db.add(document)
        self.db.flush()

        return document

    def create_version(
        self,
        *,
        version_id: UUID,
        document_id: UUID,
        version_number: int,
        parent_version_id: UUID | None,
        filename: str,
        content_type: str,
        content_hash: str,
        source: str,
        storage_reference: str | None = None,
    ) -> DocumentVersion:
        version = DocumentVersion(
            id=version_id,
            document_id=document_id,
            version_number=version_number,
            parent_version_id=parent_version_id,
            filename=filename,
            content_type=content_type,
            content_hash=content_hash,
            source=source,
            storage_reference=storage_reference,
        )

        self.db.add(version)
        self.db.flush()

        return version

    def get_latest_version(
        self,
        document_id: UUID,
    ) -> DocumentVersion | None:
        statement = (
            select(DocumentVersion)
            .where(DocumentVersion.document_id == document_id)
            .order_by(DocumentVersion.version_number.desc())
            .limit(1)
        )

        return self.db.scalars(statement).first()

    def find_by_content_hash(
        self,
        *,
        document_id: UUID,
        content_hash: str,
    ) -> DocumentVersion | None:
        statement = (
            select(DocumentVersion)
            .where(
                DocumentVersion.document_id == document_id,
                DocumentVersion.content_hash == content_hash,
            )
            .limit(1)
        )
        return self.db.scalars(statement).first()
    
    def get_version(
        self,
        document_id: UUID,
        version_id: UUID,
    ) -> DocumentVersion | None:
        """Return a specific version belonging to a document."""

        statement = (
            select(DocumentVersion)
            .where(
                DocumentVersion.document_id == document_id,
                DocumentVersion.id == version_id,
            )
            .limit(1)
        )

        return self.db.scalars(statement).first()  

    def get_versions(
        self,
        document_id: UUID,
    ) -> list[DocumentVersion]:
        """Return all versions belonging to a document."""

        statement = (
            select(DocumentVersion)
            .where(DocumentVersion.document_id == document_id)
            .order_by(DocumentVersion.version_number.asc())
        )

        return list(self.db.scalars(statement).all())  