from app.queue.run_queue import RunQueue


def _fake_client():
    import fakeredis

    return fakeredis.FakeRedis(decode_responses=True)


def test_enqueue_dequeue_round_trip():
    queue = RunQueue(_fake_client())

    enqueued = queue.enqueue(
        document_id="doc-1",
        document_version_id="v-1",
        case_id="case-1",
        idempotency_key="job-1",
    )

    assert enqueued is True
    assert queue.depth() == 1

    job = queue.dequeue(timeout_seconds=1)

    assert job == {
        "document_id": "doc-1",
        "document_version_id": "v-1",
        "case_id": "case-1",
        "idempotency_key": "job-1",
    }
    assert queue.depth() == 0


def test_duplicate_idempotency_key_is_rejected():
    queue = RunQueue(_fake_client())

    first = queue.enqueue(
        document_id="doc-1",
        document_version_id="v-1",
        case_id="case-1",
        idempotency_key="job-dup",
    )
    second = queue.enqueue(
        document_id="doc-1",
        document_version_id="v-1",
        case_id="case-1",
        idempotency_key="job-dup",
    )

    assert first is True
    assert second is False
    assert queue.depth() == 1


def test_dequeue_times_out_on_empty_queue():
    queue = RunQueue(_fake_client())

    assert queue.dequeue(timeout_seconds=1) is None
