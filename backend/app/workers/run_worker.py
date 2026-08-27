"""Docsnary run worker.

Consumes jobs from the Redis run queue and processes them through
RunService -- the same application service used by the REST API and
the MCP server. Run as a standalone process:

    python -m app.workers.run_worker

Deliberately minimal: a single-process, single-threaded consumer loop.
Horizontal scaling, retry/backoff policy, and dead-letter handling are
explicitly deferred (see PROGRESS.md) -- they are not required to
prove the T080 vertical-slice behavior (a job is enqueued once,
consumed once, and duplicate enqueue attempts are rejected by the
queue's dedupe key).
"""

import logging
from uuid import UUID

from app.db.session import SessionLocal
from app.queue.run_queue import RunQueue
from app.services.run import RunService

logger = logging.getLogger("docsnary.worker")


def process_one(job: dict) -> dict:
    db = SessionLocal()

    try:
        service = RunService(db)

        return service.run(
            document_id=UUID(job["document_id"]),
            document_version_id=UUID(job["document_version_id"]),
            case_id=job["case_id"],
        )
    finally:
        db.close()


def run_forever(queue: RunQueue | None = None) -> None:
    queue = queue or RunQueue()

    logger.info("docsnary worker started")

    while True:
        job = queue.dequeue(timeout_seconds=5)

        if job is None:
            continue

        try:
            result = process_one(job)
            logger.info("run completed run_id=%s status=%s", result.get("run_id"), result.get("status"))
        except Exception:
            logger.exception("run failed for job=%s", job)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_forever()
