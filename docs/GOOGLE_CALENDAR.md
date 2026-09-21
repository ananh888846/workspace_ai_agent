# Google Calendar — Event CRUD V1

> Trạng thái: **AccountResolver + PostgreSQL Authorization + Credential readiness gate đã triển khai; OAuth/ToolResolver/Google API vẫn PENDING**
>
> Calendar chưa được đánh dấu runtime E2E PASS cho đến khi PostgreSQL-backed authorization, OAuth và Google Calendar API verification hoàn tất.

## 1. Capability

- `calendar.read`: list/get event.
- `calendar.write`: create/update/delete event.

Google Calendar là account-backed capability. Một User có thể có nhiều Google account.

## 2. Credential boundary

Google Calendar client nhận **credential context đã được CredentialResolver cấp sau Authorization = ALLOW**.

Client không tìm account, chọn account, kiểm tra permission, đọc secret store, lưu token hoặc ghi credential vào log/audit.

```text
AccountResolver
  ↓
AuthorizationService
  ↓ ALLOW
CredentialResolver
  ↓
Google Calendar Client
  ↓
GoogleCalendarAdapter
  ↓
Google Calendar API
```

Nếu Authorization = DENY thì CredentialResolver và Google Calendar API không được gọi.

## 3. OAuth scopes

- Read: `https://www.googleapis.com/auth/calendar.readonly`
- Write: `https://www.googleapis.com/auth/calendar`

Nếu Google account trước đây chỉ được cấp Drive scope, khi bật Calendar capability có thể cần re-authorization để cấp thêm Calendar scope. Không sửa token trực tiếp.

## 4. Multiple accounts

Account selection thuộc AccountResolver:

1. Request có account hint → resolve đúng Google account.
2. Có default account → dùng default theo policy.
3. Có nhiều account nhưng không xác định được → `account_selection_required`.
4. Không để LLM tự chọn account chỉ từ tên/email trong câu.

## 5. PostgreSQL AccountResolver repository

Đã thêm `app/infrastructure/database/repositories/accounts.py`.

Repository triển khai `AccountRepository.find_candidates()` cho PostgreSQL và chỉ đọc **account metadata** từ `user_accounts`, không đọc `account_credentials`.

Candidate hợp lệ gồm:

- account do chính User sở hữu và có trạng thái `active` hoặc `pending_oauth` trong Organization;
- hoặc account được User khác delegate qua `account_grants`, với grant active, đúng Organization và còn hiệu lực theo thời gian.

Repository cũng kiểm tra Organization membership của account owner trước khi trả account. Account hint chỉ được match exact theo account ID, external account ID hoặc email; không fuzzy-match.

Repository không tự resolve credential, không authorize capability và không gọi provider API.

## 6. Authorization account access

PostgreSQL Authorization dùng cùng semantics với AccountResolver:

- Account owner có thể được Authorization chấp nhận khi account ở trạng thái `active` hoặc `pending_oauth`.
- Account delegated phải có `account_grants` hợp lệ; grant không được thay thế bằng việc chỉ biết account ID.
- `pending_oauth` không phải credential readiness. Sau Authorization = ALLOW, CredentialResolver/OAuth vẫn phải quyết định account đã đủ điều kiện gọi provider hay chưa.
- Không chuyển `pending_oauth` thành `active` giả chỉ để vượt qua Authorization.
- DENY phải chặn CredentialResolver, ToolResolver và provider API.

## 7. Provider client

`app/providers/google/calendar/client.py` nhận credential context, khởi tạo Google Calendar API v3 service và tạo `GoogleCalendarAdapter`.

Google SDK được import lazy để provider dependency không trở thành dependency bắt buộc của domain/application.

## 8. Runtime dependency

Runtime Calendar cần `google-api-python-client`. Dependency này sẽ được thêm vào dependency manifest/container image khi bắt đầu runtime Google integration.

## 9. Database

Không tạo Migration 052 cho Event CRUD. V2.1 đã có account/credential/resource/authorization/audit contracts.

Calendar không được tự tạo bảng domain riêng chỉ vì có CRUD.

## 10. Local PostgreSQL test fixture

Fixture:

`scripts/calendar/bootstrap_test_data.sql`

được thiết kế để tạo **metadata/authorization fixture**, không tạo OAuth credential.

Fixture tạo:

- Organization: `Local Calendar Test`
- User: `calendar-test@local.invalid`
- Membership: `owner`
- Permissions: `calendar.read`, `calendar.write`
- Role: `calendar_test`
- Google account metadata ở trạng thái `pending_oauth`

Fixture **không** tạo:

- `account_credentials`
- access token
- refresh token
- secret/key
- fake Calendar resource

Google account fixture dùng `local-calendar-oauth-pending` làm external ID cục bộ. Khi OAuth thật hoàn tất, account metadata phải được cập nhật qua flow ứng dụng; không dán token vào SQL fixture.

### Chạy fixture

Sau khi `migrations 001-051` đã được áp dụng:

```powershell
Get-Content .\\scripts\\calendar\\bootstrap_test_data.sql |
  docker exec -i workspace-ai-agent-postgres psql -U workspace -d workspace_ai_agent
```

Có thể kiểm tra lại:

```powershell
docker exec workspace-ai-agent-postgres psql -U workspace -d workspace_ai_agent -c "SELECT email,status FROM users WHERE email='calendar-test@local.invalid';"
docker exec workspace-ai-agent-postgres psql -U workspace -d workspace_ai_agent -c "SELECT provider,account_type,external_account_id,status FROM user_accounts WHERE external_account_id='local-calendar-oauth-pending';"
```

Nếu fixture đã tồn tại, chạy lại vẫn không tạo duplicate tenant/user/account/role mapping.

## 11. Safety

Update/delete phải xác định chính xác event.

- 0 candidate → `resource_not_found`
- 1 candidate → có thể tiếp tục authorization/tool
- >1 candidate → yêu cầu user chọn/xác nhận

Không tự chọn event để update/delete khi có nhiều candidate.

## 12. Runtime implementation status

### Đã triển khai

- PostgreSQL PermissionRepository + AuthorizationService runtime: capability/account/resource authorization gate.
- Phase 2C HTTP runtime: capability → PostgreSQL authorization decision; DENY không đi tới credential/provider.

- Provider adapter V1: `app/providers/google/calendar/adapter.py`.
- Google Calendar API client boundary: `app/providers/google/calendar/client.py`.
- Application orchestration boundary: `app/application/calendar.py`.
- Google Calendar tool boundary: `app/tools/calendar.py`.
- Core authorization runtime boundary: `app/application/core_runtime.py`.
- PostgreSQL AccountResolver repository: `app/infrastructure/database/repositories/accounts.py`; hỗ trợ resolve metadata của account `pending_oauth` để chuyển đúng sang OAuth/Credential gate.
- Phase 2B HTTP runtime wiring: `POST /api/v1/agent/chat` → AgentContext → PostgresAccountRepository → AccountResolver.
- Unit tests cho AccountResolver repository mapping và exact account hint.
- Local PostgreSQL Calendar fixture: `scripts/calendar/bootstrap_test_data.sql`.
- Contract tests xác nhận Authorization DENY không gọi CredentialResolver và ToolResolver.

### Chưa triển khai

- PostgreSQL-backed CredentialRepository / CredentialResolver.
- Core ToolResolver registry implementation.
- OAuth consent/re-authorization UI.
- Calendar webhook/push sync.
- End-to-end Google Calendar API runtime verification.

Credential readiness hiện chỉ kiểm tra credential active/chưa hết hạn và không trả encrypted_value.
Nếu chưa có credential hợp lệ, runtime trả oauth_required và chưa gọi provider.

Application service hiện chỉ định nghĩa orchestration contract và có thể chạy với dependency implementations được inject. Chưa được phép tự tạo credential/account implementation giả để bypass Core authorization.

## 13. Next runtime gate

Thứ tự triển khai được giữ cố định:

```text
Local DB fixture
  ↓
PostgreSQL AccountResolver repository  ← DONE (active + pending_oauth metadata)
  ↓
Phase 2B AccountResolver HTTP runtime  ← DONE
  ↓
PostgreSQL Authorization repository   ← DONE (active + pending_oauth account access)
  ↓
CredentialResolver / readiness gate
  ↓
OAuth nếu credential chưa sẵn sàng
  ↓
ToolResolver registry
  ↓
Google Calendar API
  ↓
E2E CRUD verification
```

Không bỏ qua bước authorization/credential để gọi Google API trực tiếp.
