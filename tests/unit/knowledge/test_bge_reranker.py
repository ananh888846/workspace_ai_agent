import sys
from types import SimpleNamespace

from app.application.knowledge.retrieval import RetrievalCandidate
from app.infrastructure.knowledge.bge_reranker import BGEReranker


def test_bge_reranker_ranks_by_model_score(monkeypatch):
    class FakeCrossEncoder:
        def __init__(self, *args, **kwargs):
            pass

        def predict(self, pairs):
            return [0.1, 0.9]

    monkeypatch.setitem(
        sys.modules, "sentence_transformers", SimpleNamespace(CrossEncoder=FakeCrossEncoder)
    )
    candidates = [
        RetrievalCandidate("p1", 0.7, "old", "v1", 0),
        RetrievalCandidate("p2", 0.6, "new", "v1", 1),
    ]
    result = BGEReranker().rerank("query", candidates)
    assert [item.point_id for item in result] == ["p2", "p1"]
