from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy.orm import Session


@contextmanager
def transaction(db: Session) -> Generator[Session, None, None]:
    """Execute database work inside a commit/rollback transaction."""

    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise