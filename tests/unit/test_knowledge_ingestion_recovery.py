from __future__ import annotations

import pytest

from app.application.knowledge.ingest import KnowledgeIngestionService
from app.domain.knowledge.source import KnowledgeSourceItem


class FakeAuthorization:
    def authorize_ingestion(self, **kwargs) -> bool:
        return True


class FakeChunker:
    def chunk(self, content: str) -> list[str]:
        return [content]


class FakeEmbedding:
    def __init__(self) -> None:
        self.calls = 0

    def embed(self, chunks: list[str]) -> list[list[float]]:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("embedding_provider_failed")
        return [[0.1, 0.2, 0.3]]


class FakeRepository:
    def __init__(self) -> None:
        self.current = None
        self.version_id = "00000000-0000-0000-0000-000000000001"
        self.created_versions = 0
        self.chunk_writes = 0
        self.unchanged = 0

    def create_source(self, item):
        return type("Source", (), {"id": "source-1"})()

    def retire_source(self, source_id):
        return []

    def current_checksum(self, source_id):
        return self.current

    def current_version_id(self, source_id):
        return self.version_id

    def create_document_version(self, source_id, item):
        self.created_versions += 1
        self.current = item.source_checksum
        return type("Version", (), {"id": self.version_id})()

    def create_chunks(self, document_version_id, organization_id, chunks):
        self.chunk_writes += 1
        return ["chunk-1"]

    def create_assets(self, document_version_id, organization_id, assets):
        return []

    def mark_unchanged(self, source_id):
        self.unchanged += 1

    def retire_previous_versions(self, source_id, current_version_id):
        return []


class FakeVectorIndex:
    def __init__(self) -> None:
        self.indexed = False
        self.upserts = 0
        self.reconciles = 0

    def is_indexed(self, document_version_id, expected_chunk_count):
        return self.indexed

    def upsert(self, chunks, vectors, document_version_id=None, organization_id=None):
        self.upserts += 1
        self.indexed = True

    def reconcile(self, document_version_id, active_chunk_indices=None):
        self.reconciles += 1

    def delete_document_version(self, document_version_id):
        pass


def make_item() -> KnowledgeSourceItem:
    return KnowledgeSourceItem(
        organization_id="org-1",
        user_account_id="user-account-1",
        provider="test",
        resource_type="document",
        external_id="doc-1",
        content="Qdrant is a derived vector index.",
        source_checksum="checksum-1",
    )


def test_ingestion_recovers_after_embedding_failure_without_duplicate_version():
    repository = FakeRepository()
    embedding = FakeEmbedding()
    vector_index = FakeVectorIndex()
    service = KnowledgeIngestionService(
        repository=repository,
        authorization=FakeAuthorization(),
        chunker=FakeChunker(),
        embedding=embedding,
        vector_index=vector_index,
    )

    with pytest.raises(RuntimeError, match="embedding_provider_failed"):
        service.ingest(make_item())

    # The first attempt already committed the canonical version.
    assert repository.created_versions == 1
    assert repository.current == "checksum-1"

    result = service.ingest(make_item())

    assert result.status == "REPAIRED_INDEX"
    assert result.document_version_id == repository.version_id
    assert repository.created_versions == 1
    assert vector_index.upserts == 1
    assert vector_index.reconciles == 1
    assert embedding.calls == 2


def test_unchanged_ingestion_skips_embedding_when_index_is_healthy():
    repository = FakeRepository()
    repository.current = "checksum-1"
    embedding = FakeEmbedding()
    vector_index = FakeVectorIndex()
    vector_index.indexed = True
    service = KnowledgeIngestionService(
        repository=repository,
        authorization=FakeAuthorization(),
        chunker=FakeChunker(),
        embedding=embedding,
        vector_index=vector_index,
    )

    result = service.ingest(make_item())

    assert result.status == "SKIPPED_UNCHANGED"
    assert result.document_version_id == repository.version_id
    assert result.chunk_count == 1
    assert embedding.calls == 0
    assert repository.unchanged == 1
