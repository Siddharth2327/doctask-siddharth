from sqlalchemy.orm import Session

from app.models.run import Run
from app.repositories.base import Repository


class RunRepository(Repository[Run]):
    def __init__(self, db: Session) -> None:
        super().__init__(db)

    def get(self, entity_id: str) -> Run | None:
        return self.db.get(Run, entity_id)

    def create(
        self,
        *,
        run_id: str,
        case_id: str,
        document_id: str,
        document_version_id: str,
        status: str = "pending",
    ) -> Run:
        run = Run(
            id=run_id,
            case_id=case_id,
            document_id=document_id,
            document_version_id=document_version_id,
            status=status,
        )

        self.db.add(run)
        self.db.flush()

        return run

    def set_status(self, run_id: str, status: str) -> Run | None:
        run = self.get(run_id)

        if run is None:
            return None

        run.status = status
        self.db.flush()

        return run

    def record_usage(
        self,
        run_id: str,
        *,
        input_tokens: int,
        output_tokens: int,
        estimated_cost: float,
    ) -> Run | None:
        run = self.get(run_id)

        if run is None:
            return None

        run.input_tokens = input_tokens
        run.output_tokens = output_tokens
        run.estimated_cost = estimated_cost
        self.db.flush()

        return run
