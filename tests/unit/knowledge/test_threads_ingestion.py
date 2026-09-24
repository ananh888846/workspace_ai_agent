from __future__ import annotations

from app.application.core_runtime import (
    AgentContext,
    AuthorizationDecision,
    ExternalAccount,
    ResolvedAccount,
)
from app.application.knowledge.threads_ingestion import ThreadsKnowledgeIngestionService
from app.application.knowledge.ingest import IngestionResult
from app.domain.knowledge.source import KnowledgeSourceItem
from app.providers.threads.client import ThreadsCredentialContext
from app.providers.threads.connector import ThreadsPage


class Accounts:
    def __init__(self):
        self.calls = []

    def resolve(self, **kwargs):
        self.calls.append(kwargs)
        return ResolvedAccount(
            account=ExternalAccount(
                id="account-1", user_id="user-1", provider="threads",
                account_type="social", external_account_id="threads-user-1",
            ),
            access_mode="owner",
            account_grant_id=None,
            organization_id="org-1",
        )


class Authorization:
    def __init__(self, allowed=True):
        self.allowed = allowed
        self.calls = []

    def authorize(self, **kwargs):
        self.calls.append(kwargs)
        return AuthorizationDecision(
            allowed=self.allowed,
            reason="authorized" if self.allowed else "account_access_denied",
            code="allow" if self.allowed else "authorization_denied",
        )


class Credentials:
    def __init__(self):
        self.calls = []

    def resolve(self, **kwargs):
        self.calls.append(kwargs)
        return type("Resolution", (), {
            "status": "ready",
            "credential_context": ThreadsCredentialContext(access_token="token"),
        })()


class Connector:
    def __init__(self):
        self.calls = []

    def list_owned_posts(self, **kwargs):
        self.calls.append(kwargs)
        item = KnowledgeSourceItem(
            organization_id="org-1", user_account_id="account-1",
            provider="threads", resource_type="post", external_id="t1",
            content="Hello", source_checksum="checksum-1",
        )
        return ThreadsPage(items=(item,), next_cursor="next-1")


class Ingestion:
    def __init__(self):
        self.items = []

    def ingest(self, item):
        self.items.append(item)
        return IngestionResult(status="COMPLETED", source_id="source-1", chunk_count=1)


def context():
    return AgentContext(
        request_id="request-1", organization_id="org-1", user_id="user-1",
        target_account="account-1",
    )


def test_authorized_flow_reaches_connector_and_knowledge():
    accounts = Accounts()
    auth = Authorization()
    credentials = Credentials()
    connector = Connector()
    ingestion = Ingestion()
    service = ThreadsKnowledgeIngestionService(
        account_resolver=accounts,
        authorization=auth,
        credentials=credentials,
        connector=connector,
        ingestion=ingestion,
    )

    result = service.ingest_owned_posts_page(context=context())

    assert result.next_cursor == "next-1"
    assert len(result.ingested) == 1
    assert len(connector.calls) == 1
    assert connector.calls[0]["credential"].access_token == "token"
    assert ingestion.items[0].external_id == "t1"


def test_denied_authorization_does_not_call_credential_or_provider():
    accounts = Accounts()
    auth = Authorization(allowed=False)
    credentials = Credentials()
    connector = Connector()
    ingestion = Ingestion()
    service = ThreadsKnowledgeIngestionService(
        account_resolver=accounts,
        authorization=auth,
        credentials=credentials,
        connector=connector,
        ingestion=ingestion,
    )

    try:
        service.ingest_owned_posts_page(context=context())
    except PermissionError as exc:
        assert str(exc) == "account_access_denied"
    else:
        raise AssertionError("authorization denial must stop the flow")

    assert credentials.calls == []
    assert connector.calls == []
    assert ingestion.items == []


def test_wrong_account_provider_is_rejected_by_account_resolution_contract():
    class WrongProviderAccounts(Accounts):
        def resolve(self, **kwargs):
            raise LookupError("account_not_found")

    connector = Connector()
    service = ThreadsKnowledgeIngestionService(
        account_resolver=WrongProviderAccounts(),
        authorization=Authorization(),
        credentials=Credentials(),
        connector=connector,
        ingestion=Ingestion(),
    )

    try:
        service.ingest_owned_posts_page(context=context())
    except LookupError as exc:
        assert str(exc) == "account_not_found"
    else:
        raise AssertionError("wrong provider/account must fail before provider call")

    assert connector.calls == []
