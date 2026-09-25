"""\nCreated/Updated: 2026-09-24 20:32 GMT+7\nMain Function: Unit tests for denied and authorized Knowledge retrieval.\n"""\n\nfrom app.application.knowledge.authorized_retrieval import AuthorizedKnowledgeRetrievalService
from app.application.knowledge.retrieval import RetrievalCandidate, KnowledgeResult


class Retrieval:
    def retrieve(self, query, *, organization_id, limit):
        return [
            RetrievalCandidate("allowed", 0.9, "yes", "v1", 0),
            RetrievalCandidate("denied", 0.8, "no", "v1", 1),
        ]


class Authorization:
    def __init__(self, allowed):
        self.allowed = allowed

    def authorize_query(self, *, user_id, organization_id):
        return self.allowed

    def filter_candidates(self, *, user_id, organization_id, candidates):
        return [
            KnowledgeResult(
                point_id="allowed",
                score=0.9,
                content="yes",
                document_version_id="v1",
                chunk_index=0,
                provider="google_drive",
                external_id="file-1",
            )
        ]


def test_k9_denied_query_returns_no_results():
    service = AuthorizedKnowledgeRetrievalService(Retrieval(), Authorization(False))
    assert service.retrieve("secret", user_id="u1", organization_id="o1") == []


def test_k9_filters_candidates_and_reconstructs_result():
    service = AuthorizedKnowledgeRetrievalService(Retrieval(), Authorization(True))
    result = service.retrieve("hello", user_id="u1", organization_id="o1")
    assert len(result) == 1
    assert result[0].provider == "google_drive"
    assert result[0].external_id == "file-1"
