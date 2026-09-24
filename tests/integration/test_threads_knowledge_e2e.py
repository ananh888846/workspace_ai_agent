from app.application.knowledge.ingest import KnowledgeIngestionService
from app.domain.knowledge.source import KnowledgeSourceItem


class Repo:
    def __init__(self):
        self.source = None
        self.checksum = None
        self.versions = 0

    def find_source(self, item):
        return self.source

    def create_source(self, item):
        self.source = type("Source", (), {"id": "source-1"})()
        return self.source

    def current_checksum(self, source_id):
        return self.checksum

    def create_document_version(self, source_id, item):
        self.versions += 1
        self.checksum = item.source_checksum
        return type("Version", (), {"id": f"version-{self.versions}"})()

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
        return [[0.1, 0.2]]


class Index:
    def __init__(self):
        self.upserts = []
        self.reconciled = []

    def upsert(self, chunks, vectors):
        self.upserts.append((chunks, vectors))

    def reconcile(self, document_version_id):
        self.reconciled.append(document_version_id)


def threads_item(checksum="threads-checksum-1"):
    return KnowledgeSourceItem(
        organization_id="org-1",
        user_account_id="account-1",
        provider="threads",
        resource_type="post",
        external_id="thread-1",
        content="Hello from Threads",
        source_checksum=checksum,
    )


def test_threads_source_item_reaches_knowledge_version_and_vector_boundary():
    repo, index = Repo(), Index()
    service = KnowledgeIngestionService(repo, Auth(), Chunker(), Embedding(), index)

    result = service.ingest(threads_item())

    assert result.status == "COMPLETED"
    assert result.chunk_count == 1
    assert repo.versions == 1
    assert index.upserts == [(["Hello from Threads"], [[0.1, 0.2]])]
    assert index.reconciled == ["version-1"]


def test_threads_source_checksum_is_idempotent():
    repo, index = Repo(), Index()
    service = KnowledgeIngestionService(repo, Auth(), Chunker(), Embedding(), index)

    first = service.ingest(threads_item())
    second = service.ingest(threads_item())

    assert first.status == "COMPLETED"
    assert second.status == "SKIPPED_UNCHANGED"
    assert repo.versions == 1
    assert len(index.upserts) == 1
