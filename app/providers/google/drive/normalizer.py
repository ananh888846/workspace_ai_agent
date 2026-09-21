import hashlib
from datetime import datetime
from typing import Any

from app.domain.knowledge.source import KnowledgeSourceItem


def _checksum(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class GoogleDriveNormalizer:
    provider = "google_drive"

    def normalize(
        self,
        raw: dict[str, Any],
        *,
        organization_id: str,
        user_account_id: str,
    ) -> KnowledgeSourceItem:
        """Map Google Drive metadata/content into the provider-neutral contract.

        Authorization, credential resolution and Drive API calls belong to
        infrastructure/application layers and are intentionally absent here.
        """
        external_id = str(raw["id"])
        content = str(raw.get("content") or "")
        mime_type = raw.get("mimeType")

        canonical_material = "
".join(
            [
                str(raw.get("name") or ""),
                content,
                str(raw.get("description") or ""),
                str(raw.get("modifiedTime") or ""),
            ]
        )

        modified_at = raw.get("modifiedTime")
        if isinstance(modified_at, str):
            modified_at = datetime.fromisoformat(modified_at.replace("Z", "+00:00"))

        return KnowledgeSourceItem(
            organization_id=organization_id,
            user_account_id=user_account_id,
            provider=self.provider,
            resource_type="file",
            external_id=external_id,
            title=raw.get("name"),
            content=content,
            mime_type=mime_type,
            source_url=raw.get("webViewLink"),
            canonical_url=raw.get("webViewLink"),
            updated_at=modified_at,
            source_revision=raw.get("version"),
            source_checksum=_checksum(canonical_material),
            metadata={
                "drive_mime_type": mime_type,
                "drive_parents": raw.get("parents", []),
            },
        )
