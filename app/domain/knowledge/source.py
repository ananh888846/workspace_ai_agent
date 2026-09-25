"""
Created/Updated: 2026-09-24 20:32 GMT+7
Main Function: Defines the provider-neutral Knowledge source item and asset reference domain contracts.
"""

\nfrom dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class KnowledgeAssetRef:
    asset_type: str
    file_name: str | None
    mime_type: str
    file_size: int
    checksum: str
    storage_backend: str
    storage_key: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeSourceItem:
    """Provider-neutral canonical input for Knowledge Ingestion."""

    organization_id: str
    user_account_id: str | None
    provider: str
    resource_type: str
    external_id: str
    content: str
    source_checksum: str
    title: str | None = None
    parent_external_id: str | None = None
    mime_type: str | None = None
    source_url: str | None = None
    canonical_url: str | None = None
    author: str | None = None
    published_at: datetime | None = None
    updated_at: datetime | None = None
    source_revision: str | None = None
    language: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    assets: tuple[KnowledgeAssetRef, ...] = ()
    deleted: bool = False

    def identity(self) -> tuple[str, str | None, str, str, str]:
        return (
            self.organization_id,
            self.user_account_id,
            self.provider,
            self.resource_type,
            self.external_id,
        )
