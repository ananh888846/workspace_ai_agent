# Google Calendar — Event CRUD V1

> Trạng thái: **Provider adapter V1 + API client boundary implemented**

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

## 5. Provider client

`app/providers/google/calendar/client.py` nhận credential context, khởi tạo Google Calendar API v3 service và tạo `GoogleCalendarAdapter`.

Google SDK được import lazy để provider dependency không trở thành dependency bắt buộc của domain/application.

## 6. Runtime dependency

Runtime Calendar cần `google-api-python-client`. Dependency này sẽ được thêm vào dependency manifest/container image khi bắt đầu runtime Google integration.

## 7. Database

Không tạo Migration 052 cho Event CRUD. V2.1 đã có account/credential/resource/authorization/audit contracts.

## 8. Safety

Update/delete phải xác định chính xác event.

- 0 candidate → `resource_not_found`
- 1 candidate → có thể tiếp tục authorization/tool
- >1 candidate → yêu cầu user chọn/xác nhận

Không tự chọn event để update/delete khi có nhiều candidate.

## 9. Chưa làm

- AccountResolver runtime implementation.
- CredentialResolver runtime implementation.
- Calendar tool registry.
- `calendar.read` application use-case.
- `calendar.write` application use-case.
- OAuth consent/re-authorization UI.
- Calendar webhook/push sync.
