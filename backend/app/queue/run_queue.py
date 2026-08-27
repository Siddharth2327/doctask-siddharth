import json

import redis

from app.core.config import settings

QUEUE_KEY = "docsnary:runs:queue"
DEDUPE_KEY_PREFIX = "docsnary:runs:dedupe:"
DEDUPE_TTL_SECONDS = 24 * 60 * 60


def get_redis() -> redis.Redis:
    return redis.Redis.from_url(settings.redis_url, decode_responses=True)


class RunQueue:
    """A minimal, real (not simulated) Redis-backed job queue.

    Deliberately simple per project guidance ("do not build an
    enterprise-grade file watcher or distributed event architecture"):
    a single Redis list as the queue, plus a SETNX-based dedupe key so
    the same idempotency key can never be enqueued twice concurrently
    (T080: "duplicate event/idempotency"). There is no retry/backoff
    policy, no priority, and no multi-consumer partitioning -- those
    are explicitly deferred (see PROGRESS.md).
    """

    def __init__(self, client: redis.Redis | None = None) -> None:
        self.client = client or get_redis()

    def enqueue(
        self,
        *,
        document_id: str,
        document_version_id: str,
        case_id: str,
        idempotency_key: str,
    ) -> bool:
        """Push a job onto the queue. Returns False (no-op) if a job
        with this idempotency_key was already enqueued recently."""

        dedupe_key = f"{DEDUPE_KEY_PREFIX}{idempotency_key}"

        is_new = self.client.set(
            dedupe_key, "1", nx=True, ex=DEDUPE_TTL_SECONDS
        )

        if not is_new:
            return False

        payload = json.dumps(
            {
                "document_id": document_id,
                "document_version_id": document_version_id,
                "case_id": case_id,
                "idempotency_key": idempotency_key,
            }
        )

        self.client.rpush(QUEUE_KEY, payload)

        return True

    def dequeue(self, timeout_seconds: int = 5) -> dict | None:
        """Blocking pop of the next job, or None on timeout."""

        result = self.client.blpop(QUEUE_KEY, timeout=timeout_seconds)

        if result is None:
            return None

        _, payload = result

        return json.loads(payload)

    def depth(self) -> int:
        return self.client.llen(QUEUE_KEY)
