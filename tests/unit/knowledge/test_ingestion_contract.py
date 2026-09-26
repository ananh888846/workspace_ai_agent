"""
Created/Updated: 2026-09-24 20:32 GMT+7
Main Function: Unit tests for Knowledge ingestion authorization, versioning, chunk persistence, and vector indexing.
"""\n\nfrom app.application.knowledge.ingest import KnowledgeIngestionService
from app.domain.knowledge.source import KnowledgeSourceItem


class Repo:
    def __init__(self):
        self.source = None
        self.versions = 0

    def find_source(self, item):
        return self.source

    def create_source(self, item):
        self.source = type("Source", (), {"id": "source-1"})()
        return self.source

    def current_checksum(self, source_id):
        return "same" if self.versions == 1 else None

    def create_document_version(self, source_id, item):
        self.versions += 1
        return type("Version", (), {"id": f"version-{self.versions}"})()

    def create_chunks(self, document_version_id, organization_id, chunks):
        self.chunks = chunks
        return [f"chunk-{i}" for i, _ in enumerate(chunks)]

    def create_assets(self, document_version_id, organization_id, assets):
        return [f"asset-{i}" for i, _ in enumerate(assets)]

    def mark_unchanged(self, source_id):
        pass


class Auth:
    def authorize_ingestion(self, **kwargs):
        return True


class Chunker:
    def chunk(self, content):
        return [content]


class Embedding:
    def embed(self, chunks):
        return [[0.0, 0.0]]


class Index:
    def upsert(self, chunks, vectors, document_version_id=None, organization_id=None):
        pass

    def reconcile(self, document_version_id):
        pass


def item(checksum="new"):
    return KnowledgeSourceItem(
        organization_id="org-1",
        user_account_id="account-1",
        provider="google_drive",
        resource_type="file",
        external_id="file-1",
        content="Xin chào Knowledge",
        source_checksum=checksum,
    )


def test_unauthorized_never_ingests():
    auth = Auth()
    auth.authorize_ingestion = lambda **kwargs: False
    service = KnowledgeIngestionService(Repo(), auth, Chunker(), Embedding(), Index())
    assert service.ingest(item()).status == "SKIPPED_UNAUTHORIZED"


def test_first_ingestion_creates_version():
    repo = Repo()
    service = KnowledgeIngestionService(repo, Auth(), Chunker(), Embedding(), Index())
    result = service.ingest(item())
    assert result.status == "COMPLETED"
    assert result.chunk_count == 1
    assert repo.chunks == ["Xin chào Knowledge"]


def test_unchanged_checksum_is_noop():
    repo = Repo()
    service = KnowledgeIngestionService(repo, Auth(), Chunker(), Embedding(), Index())
    service.ingest(item("same"))
    result = service.ingest(item("same"))
    assert result.status == "SKIPPED_UNCHANGED"
