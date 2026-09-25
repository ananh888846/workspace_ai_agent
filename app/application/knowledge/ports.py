"""\nCreated/Updated: 2026-09-24 20:32 GMT+7\nMain Function: Provider-neutral ports for Knowledge authorization, storage, parsing, chunking, embeddings, and vector indexing.\n"""\n\n"""\nCreated/Updated: 2026-09-24 20:32 GMT+7\nMain Function: Knowledge subsystem implementation or verification code for the Workspace AI Agent.\n"""\n\nfrom typing import Protocol

from app.domain.knowledge.source import KnowledgeSourceItem


class AuthorizationPort(Protocol):
    def authorize_ingestion(
        self,
        *,
        organization_id: str,
        user_account_id: str | None,
        provider: str,
        resource_type: str,
        external_id: str,
    ) -> bool: ...


class KnowledgeRepository(Protocol):
    def find_source(self, item: KnowledgeSourceItem): ...
    def create_source(self, item: KnowledgeSourceItem): ...
    def current_checksum(self, source_id: str) -> str | None: ...
    def create_document_version(self, source_id: str, item: KnowledgeSourceItem): ...
    def create_chunks(self, document_version_id: str, organization_id: str, chunks: list[str]) -> list[str]: ...
    def create_assets(self, document_version_id: str, organization_id: str, assets) -> list[str]: ...
    def mark_unchanged(self, source_id: str): ...


class StoragePort(Protocol):
    def put(self, asset, content: bytes) -> str: ...

    def get(self, storage_key: str) -> bytes: ...


class DocumentParserPort(Protocol):
    def parse(
        self,
        content: bytes,
        *,
        file_name: str,
        mime_type: str | None = None,
    ) -> str: ...


class ChunkerPort(Protocol):
    def chunk(self, content: str) -> list[str]: ...


class EmbeddingPort(Protocol):
    def embed(self, chunks: list[str]) -> list[list[float]]: ...


class VectorIndexPort(Protocol):
    def upsert(
        self,
        chunks: list[str],
        vectors: list[list[float]],
        document_version_id: str | None = None,
        organization_id: str | None = None,
    ) -> None: ...
    def reconcile(self, document_version_id: str) -> None: ...
