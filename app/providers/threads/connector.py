from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.knowledge.source import KnowledgeSourceItem
from app.providers.threads.client import (
    ThreadsClient,
    ThreadsCredentialContext,
)
from app.providers.threads.normalizer import ThreadsNormalizer


POST_FIELDS = "id,text,timestamp,media_product_type,media_type,permalink,shortcode,username,is_quote_post,has_replies,is_reply"
REPLY_FIELDS = POST_FIELDS + ",is_reply_owned_by_me,root_post,replied_to"


@dataclass(frozen=True)
class ThreadsPage:
    items: tuple[KnowledgeSourceItem, ...]
    next_cursor: str | None


class ThreadsSourceConnector:
    """Provider-specific read connector producing canonical Knowledge items."""

    provider = "threads"

    def __init__(self, client: ThreadsClient, normalizer: ThreadsNormalizer | None = None) -> None:
        self._client = client
        self._normalizer = normalizer or ThreadsNormalizer()

    def list_owned_posts(
        self,
        *,
        credential: ThreadsCredentialContext,
        organization_id: str,
        user_account_id: str,
        after: str | None = None,
    ) -> ThreadsPage:
        payload = self._client.list_owned_threads(
            credential=credential,
            fields=POST_FIELDS,
            after=after,
        )
        return self._normalize_page(
            payload,
            organization_id=organization_id,
            user_account_id=user_account_id,
            resource_type="post",
        )

    def fetch_post(
        self,
        *,
        credential: ThreadsCredentialContext,
        organization_id: str,
        user_account_id: str,
        thread_id: str,
    ) -> KnowledgeSourceItem:
        raw = self._client.get_thread(
            thread_id=thread_id,
            credential=credential,
            fields=POST_FIELDS,
        )
        return self._normalizer.normalize(
            raw,
            organization_id=organization_id,
            user_account_id=user_account_id,
            resource_type="post",
        )

    def fetch_replies(
        self,
        *,
        credential: ThreadsCredentialContext,
        organization_id: str,
        user_account_id: str,
        thread_id: str,
        after: str | None = None,
    ) -> ThreadsPage:
        payload = self._client.get_replies(
            thread_id=thread_id,
            credential=credential,
            fields=REPLY_FIELDS,
            after=after,
        )
        return self._normalize_page(
            payload,
            organization_id=organization_id,
            user_account_id=user_account_id,
            resource_type="reply",
        )

    def _normalize_page(
        self,
        payload: dict[str, Any],
        *,
        organization_id: str,
        user_account_id: str,
        resource_type: str,
    ) -> ThreadsPage:
        data = payload.get("data", [])
        if not isinstance(data, list):
            raise ValueError("threads_invalid_data")
        items = tuple(
            self._normalizer.normalize(
                item,
                organization_id=organization_id,
                user_account_id=user_account_id,
                resource_type=resource_type,
            )
            for item in data
            if isinstance(item, dict)
        )
        paging = payload.get("paging") or {}
        cursors = paging.get("cursors") if isinstance(paging, dict) else None
        next_cursor = cursors.get("after") if isinstance(cursors, dict) else None
        return ThreadsPage(items=items, next_cursor=next_cursor)
