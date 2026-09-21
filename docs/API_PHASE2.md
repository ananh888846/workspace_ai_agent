# API Phase 2 — Agent Chat Contract

## Trạng thái

- Phase 2A HTTP contract: **DONE**
- Phase 2B AccountResolver runtime: **DONE**
- Phase 2C PostgreSQL Authorization runtime: **DONE**
- Phase 2D Web Chat gọi real API: **NEXT**

## Phase 2B — AccountResolver

POST /api/v1/agent/chat nhận account_hint. Khi có account_hint, runtime yêu cầu:
- X-User-ID
- X-Organization-ID

Hai header này chỉ là AgentContext test/runtime context; không tự cấp quyền.

Flow:

```text
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
```

Phase 2B chỉ resolve account metadata. Không đọc account_credentials, không authorize, không resolve tool và không gọi Google API.

## Phase 2C — PostgreSQL Authorization runtime

Khi request có capability, runtime authorization được thực hiện sau AccountResolver nếu account hint có mặt.

```text
AccountResolver
      ↓
AuthorizationService
      ↓
PostgresPermissionRepository
      ├── Capability Permission
      ├── Account Access
      └── Resource Permission nếu có target_resource
      ↓
ALLOW / DENY
      ↓
chỉ ALLOW mới được CredentialResolver
```

### Capability Permission

calendar.read được tách thành resource=calendar và action=read.

Permission được kiểm tra qua user_roles → role_permissions → permissions(resource, action).

Role không có permission tương ứng phải bị DENY.

### Account Access

Account phải active; thuộc User hoặc có account_grants hợp lệ; owner/grantee và account phải nằm trong cùng Organization; grant phải active, chưa bị revoke và còn hiệu lực theo thời gian.

PostgresPermissionRepository không đọc account_credentials.

### Resource Access

Nếu target_resource có mặt, AuthorizationService yêu cầu resource_permissions: resource cùng Organization; user là active member; action khớp; effect=allow; permission chưa hết hạn.

Thiếu resource permission → resource_access_denied.

### DENY boundary

Khi Authorization = DENY: không gọi CredentialResolver; không đọc account_credentials; không resolve Tool; không gọi provider API.

Phase 2C hiện chỉ trả execution metadata; chưa thực hiện provider call.

## HTTP fields cho Phase 2C

Request:

```json
{
  "message": "Đọc lịch",
  "conversation_id": "optional-id",
  "account_hint": "abc@gmail.com",
  "capability": "calendar.read",
  "action": "read",
  "target_resource": "optional-resource-id"
}
```

Runtime context: X-User-ID và X-Organization-ID.

Nếu có account_hint, AccountResolver phải resolve account trước Authorization.

Nếu có capability hoặc target_resource nhưng thiếu runtime context, API trả HTTP 400.

## Phase 2D

```text
Web Chat
   ↓
POST /api/v1/agent/chat
   ↓
AgentContext
   ↓
AccountResolver
   ↓
AuthorizationService
   ↓
Debug execution metadata
```

Phase 2D mới nối workspace_ai_agent_web vào endpoint thật. Không đưa Google OAuth/provider vào Web trước khi Authorization gate được kiểm chứng.