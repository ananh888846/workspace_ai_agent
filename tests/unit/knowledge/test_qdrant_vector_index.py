"""
Created/Updated: 2026-09-24 20:32 GMT+7
Main Function: Unit tests for Qdrant collection creation, upsert, and non-destructive reconciliation.
"""

from app.infrastructure.knowledge.qdrant import QdrantVectorIndex, QdrantVectorStoreError


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


def test_qdrant_reconcile_deletes_stale_chunks(monkeypatch):
    calls = []
    index = QdrantVectorIndex("http://qdrant", "knowledge")

    def request(method, path, payload=None):
        calls.append((method, path, payload))
        if method == "POST" and path.endswith("/points/scroll"):
            return {
                "result": {
                    "points": [
                        {"id": "keep", "payload": {"chunk_index": 0}},
                        {"id": "stale", "payload": {"chunk_index": 1}},
                    ]
                }
            }
        return {"result": {"status": "ok"}}

    monkeypatch.setattr(index, "_request", request)
    index.reconcile("11111111-1111-1111-1111-111111111111", [0])

    assert calls[0][0] == "POST"
    assert calls[0][1].endswith("/points/scroll")
    assert calls[1][0] == "POST"
    assert calls[1][1].endswith("/points/delete?wait=true")
    assert calls[1][2] == {"points": ["stale"]}


def test_qdrant_reconcile_paginates_all_chunks(monkeypatch):
    calls = []
    index = QdrantVectorIndex("http://qdrant", "knowledge")

    def request(method, path, payload=None):
        calls.append((method, path, payload))
        if method == "POST" and path.endswith("/points/scroll"):
            if payload.get("offset") is None:
                return {
                    "result": {
                        "points": [
                            {"id": "keep-page-1", "payload": {"chunk_index": 0}},
                        ],
                        "next_page_offset": "page-2",
                    }
                }
            assert payload["offset"] == "page-2"
            return {
                "result": {
                    "points": [
                        {"id": "stale-page-2", "payload": {"chunk_index": 1001}},
                    ],
                    "next_page_offset": None,
                }
            }
        return {"result": {"status": "ok"}}

    monkeypatch.setattr(index, "_request", request)
    index.reconcile("11111111-1111-1111-1111-111111111111", [0])

    scrolls = [call for call in calls if call[1].endswith("/points/scroll")]
    deletes = [call for call in calls if call[1].endswith("/points/delete?wait=true")]
    assert len(scrolls) == 2
    assert deletes[0][2] == {"points": ["stale-page-2"]}


def test_qdrant_delete_document_version_uses_version_filter(monkeypatch):
    calls = []
    index = QdrantVectorIndex("http://qdrant", "knowledge")
    monkeypatch.setattr(
        index,
        "_request",
        lambda method, path, payload=None: calls.append((method, path, payload))
        or {"result": {"status": "ok"}},
    )

    index.delete_document_version("11111111-1111-1111-1111-111111111111")

    assert calls[0][0] == "POST"
    assert calls[0][1].endswith("/points/delete?wait=true")
    assert calls[0][2]["filter"]["must"][0]["key"] == "document_version_id"
