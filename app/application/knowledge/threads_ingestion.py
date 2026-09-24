from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.application.core_runtime import (
    AgentContext,
    AuthorizationService,
    CredentialResolver,
    AccountResolver,
    CoreAuthorizationError,
)
from app.application.knowledge.ingest import IngestionResult, KnowledgeIngestionService
from app.providers.threads.connector import ThreadsPage, ThreadsSourceConnector
from app.providers.threads.client import ThreadsCredentialContext


class ThreadsAccountReader(Protocol):
    def list_owned_posts(
        self,
        *,
        credential: ThreadsCredentialContext,
        organization_id: str,
        user_account_id: str,
        after: str | None = None,
    ) -> ThreadsPage: ...


@dataclass(frozen=True)
class ThreadsIngestionPageResult:
    ingested: tuple[IngestionResult, ...]
    next_cursor: str | None


class ThreadsKnowledgeIngestionService:
    """Composition boundary: account → auth → credential → Threads → Knowledge."""

    def __init__(
        self,
        *,
        account_resolver: AccountResolver,
        authorization: AuthorizationService,
        credentials: CredentialResolver,
        connector: ThreadsAccountReader,
        ingestion: KnowledgeIngestionService,
    ) -> None:
        self._account_resolver = account_resolver
        self._authorization = authorization
        self._credentials = credentials
        self._connector = connector
        self._ingestion = ingestion

    def ingest_owned_posts_page(
        self,
        *,
        context: AgentContext,
        after: str | None = None,
        account_hint: str | None = None,
        capability: str = "knowledge.read",
    ) -> ThreadsIngestionPageResult:
        account = self._account_resolver.resolve(
            user_id=context.user_id,
            organization_id=context.organization_id,
            provider="threads",
            account_hint=account_hint or context.target_account,
        )
        authorized_context = AgentContext(
            request_id=context.request_id,
            organization_id=context.organization_id,
            user_id=context.user_id,
            session_id=context.session_id,
            device_id=context.device_id,
            capability=capability,
            action="read",
            target_account=account.account.id,
            target_resource=context.target_resource,
            target_package=context.target_package,
            metadata=context.metadata,
        )
        decision = self._authorization.authorize(
            context=authorized_context,
            resolved_account=account,
            account=account.account,
        )
        if not decision.allowed:
            raise CoreAuthorizationError(decision.reason)

        credential = self._credentials.resolve(
            decision=decision,
            account=account.account,
        )
        if credential.status != "ready" or not isinstance(
            credential.credential_context, ThreadsCredentialContext
        ):
            raise RuntimeError("threads_oauth_required")

        page = self._connector.list_owned_posts(
            credential=credential.credential_context,
            organization_id=account.organization_id,
            user_account_id=account.account.id,
            after=after,
        )
        results = tuple(self._ingestion.ingest(item) for item in page.items)
        return ThreadsIngestionPageResult(ingested=results, next_cursor=page.next_cursor)
