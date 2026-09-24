# Threads Source Connector V1 — Implementation

> Status: CREDENTIAL BOUNDARY IMPLEMENTED — UNIT TESTS ADDED — LIVE PROVIDER SMOKE TEST NOT RUN
> Date: 2026-09-24
> Architecture source of truth: workspace-ai-agent-ecosystem / ARCHITECTURE/THREADS_CONNECTOR_CONTRACT_V1.md

## Scope
The Backend now contains a read-oriented Threads provider boundary for Knowledge ingestion.

Implemented:
- Threads HTTP client boundary;
- already-authorized Threads credential context;\n- provider-scoped Meta credential repository;
- owned Threads post listing;
- single Thread fetch;
- paginated reply fetch;
- provider payload → KnowledgeSourceItem normalization;
- opaque pagination cursor propagation;
- reply parent_external_id mapping;
- common provider error codes;
- unit tests for normalization and pagination.

## Files
- app/providers/threads/client.py
- app/providers/threads/normalizer.py
- app/providers/threads/connector.py
- tests/unit/providers/test_threads_connector.py

## Security boundary
The connector does not read account_credentials, decrypt credentials, perform authorization, select accounts, call Agent Runtime, call LLM, call Qdrant or create Knowledge versions.\n\nCredential resolution is now provider-scoped: the Meta repository verifies user_accounts.provider = threads before returning an access-token-only MetaCredentialContext. Credential resolution remains behind the existing CredentialResolver and cannot run after a denied AuthorizationDecision.
The connector receives ThreadsCredentialContext only after the application authorization/credential boundary.

## Runtime boundary
The connector is intentionally not registered in app/main.py or AgentRuntime yet.
The credential boundary is now implemented. A production ingestion composition root still needs to connect:
AccountResolver → AuthorizationService → CredentialResolver → ThreadsSourceConnector → KnowledgeIngestionService.
This is deliberate: connector code is implemented before production wiring so the authorization and ingestion runtime can be composed without bypassing existing security boundaries.

## Provider behavior
The current client uses the Threads Graph API base URL and supports:
- GET /me/threads;
- GET /{thread_id};
- GET /{thread_id}/replies.
Provider pagination cursors remain opaque.

## Verification state
Verified by source inspection:
- connector follows the provider-neutral KnowledgeSourceItem contract;
- connector does not own authorization/credential storage;
- replies preserve provider parent identity;
- cursor is returned separately from canonical Knowledge identity.

Not yet verified:
- real Threads OAuth configuration;\n- runtime composition against a real Meta credential row;
- real authorized account;
- live API request;
- live provider rate-limit behavior;
- end-to-end Threads → Knowledge SQL/version/chunk/vector ingestion.

## Next implementation step
1. Add a provider-neutral credential repository/context path for Meta/Threads without reusing Google-specific credential types.
2. Compose AccountResolver + AuthorizationService + CredentialResolver + ThreadsSourceConnector.
3. Connect connector output to KnowledgeIngestionService.
4. Add integration tests proving authorization denial prevents provider calls.
5. Run controlled live Threads smoke test with a valid app/account.
6. Verify ingestion persistence and idempotency.
7. Update ecosystem status from IMPLEMENTED/CHƯA XÁC MINH to VERIFIED only after runtime evidence.

Facebook remains blocked on capability verification and is not implemented by this change.