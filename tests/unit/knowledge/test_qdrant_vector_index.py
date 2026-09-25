"""\nCreated/Updated: 2026-09-24 20:32 GMT+7\nMain Function: Unit tests for Qdrant collection creation, upsert, and non-destructive reconciliation.\n"""\n\nfrom app.infrastructure.knowledge.qdrant import QdrantVectorIndex, QdrantVectorStoreError


def test_qdrant_upsert_creates_collection_and_points(monkeypatch):
    calls = []

    def request(method, path, payload=None):
        calls.append((method, path, payload))
        if method == "GET":
            raise QdrantVectorStoreError("qdrant_http_404")
        return {"result": {"status": "ok"}}

    index = QdrantVectorIndex("http://qdrant", "knowledge")
    monkeypatch.setattr(index, "_request", request)

    index.upsert(
        ["hello", "world"],
        [[0.1, 0.2], [0.3, 0.4]],
        "11111111-1111-1111-1111-111111111111",
    )

    assert calls[0][0] == "GET"
    assert calls[1][0] == "PUT"
    assert calls[1][2]["vectors"]["size"] == 2
    assert calls[2][0] == "PUT"
    assert len(calls[2][2]["points"]) == 2


def test_qdrant_reconcile_is_non_destructive(monkeypatch):
    calls = []
    index = QdrantVectorIndex("http://qdrant", "knowledge")
    monkeypatch.setattr(
        index,
        "_request",
        lambda method, path, payload=None: calls.append((method, path, payload))
        or {"result": {"status": "ok"}},
    )

    index.reconcile("11111111-1111-1111-1111-111111111111")

    assert calls == []
