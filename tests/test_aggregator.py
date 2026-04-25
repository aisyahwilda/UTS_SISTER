import time

from fastapi.testclient import TestClient

from src.main import create_app


def _base_event(event_id: str, topic: str = "orders"):
    return {
        "topic": topic,
        "event_id": event_id,
        "timestamp": "2026-04-24T10:00:00Z",
        "source": "publisher-A",
        "payload": {"value": 1},
    }


def _wait_until_processed(client: TestClient, expected_unique: int, timeout: float = 2.5):
    start = time.time()
    while time.time() - start <= timeout:
        snapshot = client.get("/stats").json()
        if snapshot["unique_processed"] >= expected_unique:
            return snapshot
        time.sleep(0.01)
    return client.get("/stats").json()


def test_publish_single_event_and_retrieve(tmp_path):
    db_path = tmp_path / "dedup.db"
    app = create_app(str(db_path))

    with TestClient(app) as client:
        response = client.post("/publish", json=_base_event("evt-1"))
        assert response.status_code == 200
        _wait_until_processed(client, expected_unique=1)

        events = client.get("/events", params={"topic": "orders"}).json()
        assert len(events) == 1
        assert events[0]["event_id"] == "evt-1"


def test_dedup_drops_duplicate_event(tmp_path):
    db_path = tmp_path / "dedup.db"
    app = create_app(str(db_path))

    with TestClient(app) as client:
        event = _base_event("evt-dup")
        client.post("/publish", json=event)
        client.post("/publish", json=event)

        snapshot = _wait_until_processed(client, expected_unique=1)
        assert snapshot["received"] == 2
        assert snapshot["unique_processed"] == 1
        assert snapshot["duplicate_dropped"] >= 1


def test_batch_publish_with_duplicates(tmp_path):
    db_path = tmp_path / "dedup.db"
    app = create_app(str(db_path))

    batch = [
        _base_event("evt-1"),
        _base_event("evt-2"),
        _base_event("evt-1"),
    ]

    with TestClient(app) as client:
        response = client.post("/publish", json=batch)
        assert response.status_code == 200
        assert response.json()["count"] == 3

        snapshot = _wait_until_processed(client, expected_unique=2)
        assert snapshot["received"] == 3
        assert snapshot["unique_processed"] == 2
        assert snapshot["duplicate_dropped"] == 1


def test_dedup_persists_after_restart(tmp_path):
    db_path = tmp_path / "dedup.db"

    first_app = create_app(str(db_path))
    with TestClient(first_app) as client:
        client.post("/publish", json=_base_event("evt-persist"))
        first_snapshot = _wait_until_processed(client, expected_unique=1)
        assert first_snapshot["unique_processed"] == 1

    second_app = create_app(str(db_path))
    with TestClient(second_app) as client:
        client.post("/publish", json=_base_event("evt-persist"))
        time.sleep(0.05)
        second_snapshot = client.get("/stats").json()
        assert second_snapshot["received"] == 1
        assert second_snapshot["unique_processed"] == 0
        assert second_snapshot["duplicate_dropped"] == 1


def test_event_schema_validation_errors(tmp_path):
    db_path = tmp_path / "dedup.db"
    app = create_app(str(db_path))

    with TestClient(app) as client:
        missing_topic = {
            "event_id": "evt-x",
            "timestamp": "2026-04-24T10:00:00Z",
            "source": "publisher-A",
            "payload": {},
        }
        invalid_timestamp = {
            "topic": "orders",
            "event_id": "evt-y",
            "timestamp": "bukan-iso8601",
            "source": "publisher-A",
            "payload": {},
        }

        assert client.post("/publish", json=missing_topic).status_code == 422
        assert client.post("/publish", json=invalid_timestamp).status_code == 422


def test_stats_and_events_consistency(tmp_path):
    db_path = tmp_path / "dedup.db"
    app = create_app(str(db_path))

    events = [
        _base_event("evt-a", topic="orders"),
        _base_event("evt-b", topic="orders"),
        _base_event("evt-c", topic="payments"),
    ]

    with TestClient(app) as client:
        client.post("/publish", json=events)
        snapshot = _wait_until_processed(client, expected_unique=3)

        all_events = client.get("/events").json()
        assert snapshot["received"] == 3
        assert snapshot["unique_processed"] == 3
        assert set(snapshot["topics"]) == {"orders", "payments"}
        assert len(all_events["orders"]) == 2
        assert len(all_events["payments"]) == 1


def test_small_stress_batch_performance(tmp_path):
    db_path = tmp_path / "dedup.db"
    app = create_app(str(db_path))

    total_events = 1200
    unique_events = 960
    payload = []

    for index in range(total_events):
        logical_id = f"evt-{index % unique_events}"
        payload.append(_base_event(logical_id, topic="stress"))

    with TestClient(app) as client:
        start = time.perf_counter()
        response = client.post("/publish", json=payload)
        duration = time.perf_counter() - start

        assert response.status_code == 200
        snapshot = _wait_until_processed(client, expected_unique=unique_events, timeout=8.0)

        assert snapshot["received"] == total_events
        assert snapshot["unique_processed"] == unique_events
        assert snapshot["duplicate_dropped"] == total_events - unique_events
        assert duration < 2.0


def test_five_thousand_events_with_twenty_percent_duplicates(tmp_path):
    db_path = tmp_path / "dedup.db"
    app = create_app(str(db_path))

    total_events = 5000
    unique_events = 4000
    payload = []

    for index in range(total_events):
        logical_id = f"evt-{index % unique_events}"
        payload.append(_base_event(logical_id, topic="scale"))

    with TestClient(app) as client:
        start = time.perf_counter()
        response = client.post("/publish", json=payload)
        duration = time.perf_counter() - start

        assert response.status_code == 200
        snapshot = _wait_until_processed(client, expected_unique=unique_events, timeout=20.0)

        assert snapshot["received"] == total_events
        assert snapshot["unique_processed"] == unique_events
        assert snapshot["duplicate_dropped"] == total_events - unique_events
        assert duration < 6.0
