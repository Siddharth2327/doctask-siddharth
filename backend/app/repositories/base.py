from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from sqlalchemy.orm import Session


T = TypeVar("T")


class Repository(ABC, Generic[T]):
    """Base repository contract for persistence operations."""

    def __init__(self, db: Session) -> None:
        self.db = db

    @abstractmethod
    def get(self, entity_id: str) -> T | None:
        """Return an entity by ID or None when it does not exist."""
        raise NotImplementedError