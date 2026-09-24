from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

from app.domain.knowledge.source import KnowledgeSourceItem


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _checksum(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ThreadsNormalizer:
    provider = "threads"

    def normalize(
        self,
        raw: dict[str, Any],
        *,
        organization_id: str,
        user_account_id: str,
        resource_type: str = "post",
    ) -> KnowledgeSourceItem:
        external_id = str(raw["id"])
        content = str(raw.get("text") or "")
        parent = raw.get("replied_to")
        parent_external_id = None
        if isinstance(parent, dict) and parent.get("id") is not None:
            parent_external_id = str(parent["id"])

        canonical_material = {
            "id": external_id,
            "resource_type": resource_type,
            "text": content,
            "timestamp": raw.get("timestamp"),
            "permalink": raw.get("permalink"),
            "username": raw.get("username"),
            "root_post": raw.get("root_post"),
            "replied_to": raw.get("replied_to"),
        }

        metadata = {
            "media_product_type": raw.get("media_product_type"),
            "media_type": raw.get("media_type"),
            "shortcode": raw.get("shortcode"),
            "is_quote_post": raw.get("is_quote_post"),
            "has_replies": raw.get("has_replies"),
            "is_reply": raw.get("is_reply"),
            "is_reply_owned_by_me": raw.get("is_reply_owned_by_me"),
        }
        metadata = {key: value for key, value in metadata.items() if value is not None}

        return KnowledgeSourceItem(
            organization_id=organization_id,
            user_account_id=user_account_id,
            provider=self.provider,
            resource_type=resource_type,
            external_id=external_id,
            parent_external_id=parent_external_id,
            title=None,
            content=content,
            mime_type="text/plain",
            source_url=raw.get("permalink"),
            canonical_url=raw.get("permalink"),
            author=raw.get("username"),
            published_at=_parse_datetime(raw.get("timestamp")),
            updated_at=_parse_datetime(raw.get("timestamp")),
            source_revision=None,
            source_checksum=_checksum(canonical_material),
            metadata=metadata,
        )
