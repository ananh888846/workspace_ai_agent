from typing import Protocol

from app.domain.knowledge.source import KnowledgeSourceItem


class ProviderAdapter(Protocol):
    provider: str

    def normalize(self, raw: object, *, organization_id: str, user_account_id: str | None) -> KnowledgeSourceItem:
        """Convert provider payload to the canonical KnowledgeSourceItem."""
        ...
