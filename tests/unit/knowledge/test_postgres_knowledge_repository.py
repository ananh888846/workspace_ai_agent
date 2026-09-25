from app.domain.knowledge.source import KnowledgeSourceItem
from app.infrastructure.database.repositories.knowledge import (
    PostgresKnowledgeRepository,
)


class Cursor:
    def __init__(self, rows):
        self.rows = list(rows)
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, query, params):
        self.calls.append((query, params))

    def fetchone(self):
        return self.rows.pop(0) if self.rows else None


class Connection:
    def __init__(self, rows):
        self.cursor_obj = Cursor(rows)
        self.commits = 0
        self.rollbacks = 0

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


def item():
    return KnowledgeSourceItem(
        organization_id="org-1",
        user_account_id="account-1",
        provider="google_drive",
        resource_type="file",
        external_id="file-1",
        title="Knowledge file",
        content="Canonical knowledge",
        source_revision="7",
        source_checksum="checksum-1",
        metadata={"origin": "drive"},
    )


def test_find_source_is_tenant_account_provider_scoped():
    connection = Connection([("source-1",)])
    repo = PostgresKnowledgeRepository(connection)

    result = repo.find_source(item())

    assert result.id == "source-1"
    query, params = connection.cursor_obj.calls[0]
    assert "organization_id = %s" in query
    assert "user_account_id IS NOT DISTINCT FROM %s" in query
    assert params == ["org-1", "account-1", "google_drive", "file", "file-1"]


def test_create_source_persists_provenance_metadata():
    connection = Connection([None, ("source-1",)])
    repo = PostgresKnowledgeRepository(connection)

    result = repo.create_source(item())

    assert result.id == "source-1"
    assert connection.commits == 1
    query, params = connection.cursor_obj.calls[-1]
    assert "INSERT INTO knowledge_sources" in query
    assert params[0:5] == ["org-1", "account-1", "google_drive", "file", "file-1"]


def test_current_checksum_reads_latest_version():
    connection = Connection([("checksum-7",)])
    repo = PostgresKnowledgeRepository(connection)

    assert repo.current_checksum("source-1") == "checksum-7"
    query, params = connection.cursor_obj.calls[0]
    assert "ORDER BY kdvv.version_no DESC" in query
    assert params == ["source-1"]


def test_create_document_version_persists_canonical_content_and_primary_provenance():
    # No existing document, then INSERT document, MAX(version), INSERT version.
    connection = Connection([
        None,       # document lookup through provenance
        None,       # legacy document lookup
        ("doc-1",), # document INSERT
        (1,),       # next version number
        ("version-2",),  # version INSERT
    ])
    repo = PostgresKnowledgeRepository(connection)

    result = repo.create_document_version("source-1", item())

    assert result.id == "version-2"
    assert connection.commits == 1
    statements = [call[0] for call in connection.cursor_obj.calls]
    assert any("INSERT INTO knowledge_documents" in sql for sql in statements)
    assert any("INSERT INTO knowledge_document_versions" in sql for sql in statements)
    assert any("INSERT INTO knowledge_document_version_sources" in sql for sql in statements)
    assert any("canonical_content" in sql for sql in statements)


def test_create_document_version_rolls_back_on_database_error():
    connection = Connection([None])
    repo = PostgresKnowledgeRepository(connection)

    # The fake cursor has no row for the document INSERT, so the method fails
    # while the transaction boundary must still roll back.
    try:
        repo.create_document_version("source-1", item())
    except Exception:
        pass
    else:
        raise AssertionError("expected repository failure")

    assert connection.rollbacks == 1


def test_create_chunks_persists_version_scoped_content_and_stable_point_id():
    connection = Connection([("chunk-1",)])
    repo = PostgresKnowledgeRepository(connection)

    result = repo.create_chunks(
        "11111111-1111-7111-8111-111111111111",
        "org-1",
        ["first chunk"],
    )

    assert result == ["chunk-1"]
    assert connection.commits == 1
    query, params = connection.cursor_obj.calls[0]
    assert "knowledge_chunks" in query
    assert "document_version_id" in query
    assert params[0] == 0
    assert params[3] == "org-1"
    assert params[5] == "11111111-1111-7111-8111-111111111111"


def test_create_assets_persists_storage_metadata():
    class Asset:
        asset_type = "document"
        file_name = "file.pdf"
        mime_type = "application/pdf"
        file_size = 42
        checksum = "asset-checksum"
        storage_backend = "local"
        storage_key = "knowledge/file.pdf"
        metadata = {"page": 1}

    connection = Connection([("asset-1",)])
    repo = PostgresKnowledgeRepository(connection)

    result = repo.create_assets(
        "version-1",
        "org-1",
        [Asset()],
    )

    assert result == ["asset-1"]
    assert connection.commits == 1
    query, params = connection.cursor_obj.calls[0]
    assert "knowledge_assets" in query
    assert params[0:3] == ["org-1", "version-1", "document"]
