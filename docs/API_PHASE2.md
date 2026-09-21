# API Phase 2 — Agent Chat Contract

## Trạng thái

- Phase 2A HTTP contract: DONE
- Phase 2B AccountResolver runtime: DONE
- Phase 2C Authorization runtime: NEXT

## Phase 2B

POST /api/v1/agent/chat nhận account_hint. Khi có account_hint, runtime yêu cầu:

- X-User-ID
- X-Organization-ID

Hai header này chỉ là AgentContext test/runtime context; không tự cấp quyền.

Flow:

Web/API
  ↓
AgentContext
  ↓
PostgresAccountRepository
  ↓
AccountResolver
  ├── 0 account → account_not_found
  ├── 1 account → resolved
  └── >1 account → account_selection_required
  ↓
Không gọi credential/provider

Phase 2B chỉ resolve account metadata. Không đọc account_credentials,
không authorize, không resolve tool và không gọi Google API.

## Phase 2C

AccountResolver
  ↓
AuthorizationService
  ├── capability permission
  ├── account access
  └── resource access
  ↓
ALLOW / DENY
  ↓
chỉ sau ALLOW mới được CredentialResolver
