from app.infrastructure.knowledge.qdrant import QdrantVectorIndex


def test_qdrant_upsert_creates_collection_and_points(monkeypatch):
    calls = []

    def request(method, path, payload=None):
        calls.append((method, path, payload))
        if method == "GET":
            from app.infrastructure.knowledge.qdrant import QdrantVectorStoreError
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


def test_qdrant_reconcile_deletes_version_points(monkeypatch):
    calls = []
    index = QdrantVectorIndex("http://qdrant", "knowledge")
    monkeypatch.setattr(
        index,
        "_request",
        lambda method, path, payload=None: calls.append((method, path, payload))
        or {"result": {"status": "ok"}},
    )

    index.reconcile("11111111-1111-1111-1111-111111111111")

    assert calls[0][0] == "POST"
    assert "points/delete" in calls[0][1]
    assert calls[0][2]["filter"]["must"][0]["key"] == "document_version_id"
