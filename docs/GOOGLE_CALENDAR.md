# Google Calendar — Event CRUD V1

> Trạng thái: **Calendar Read V1 — CLOSED / E2E PASS** · **Calendar Write V1 — CLOSED / E2E PASS**

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
Google Calendar Tool
  ↓
GoogleCalendarAdapter
  ↓
Google Calendar API
```

Nếu Authorization = DENY thì CredentialResolver và Google Calendar API không được gọi.

## 3. Quy trình OAuth thao tác

Khi cần OAuth lại Google account, thực hiện theo runbook chuẩn `docs/GOOGLE_OAUTH.md`. Không tự tạo URL hoặc tự đưa `x-user-id`/`x-organization-id` vào `.env`.

## 4. OAuth scopes

- Read: `https://www.googleapis.com/auth/calendar.readonly`
- Write: `https://www.googleapis.com/auth/calendar`

Bộ scope của từng phiên OAuth phải được giữ nguyên từ lúc tạo authorization URL đến lúc callback đổi authorization code. OAuth state chứa bộ scope đã yêu cầu cùng `code_verifier`, và callback dựng lại `Flow` bằng chính bộ scope đó.

Google có thể trả về thêm scope đã được cấp trước đó khi dùng `include_granted_scopes=true`. Scope thực tế do Google trả về được lưu trong `account_credentials.scopes`.

## 5. Multiple accounts

Account selection thuộc AccountResolver:

1. Request có account hint → resolve đúng Google account.
2. Có default account → dùng default theo policy.
3. Có nhiều account nhưng không xác định được → `account_selection_required`.
4. Không để LLM tự chọn account chỉ từ tên/email trong câu.

## 6. Authorization account access

PostgreSQL Authorization dùng cùng semantics với AccountResolver. Account owner/delegated account phải qua Authorization trước CredentialResolver.

- `pending_oauth` không phải credential readiness.
- DENY phải chặn CredentialResolver, ToolResolver và provider API.
- Create/update/delete đều phải đi qua capability `calendar.write`.

## 7. Provider client

`app/providers/google/calendar/client.py` nhận credential context, khởi tạo Google Calendar API v3 service và tạo `GoogleCalendarAdapter`.

`app/providers/google/calendar/adapter.py` hỗ trợ:

- `list_events`
- `get_event`
- `create_event`
- `update_event`
- `delete_event`

## 8. Database và thời gian

Không tạo Migration riêng cho Calendar Event CRUD V1. Calendar event là resource của Google; agent không tự tạo bảng event chỉ để mirror provider.

**Nguyên tắc thời gian toàn hệ thống:**

- Timestamp lưu trong database → **UTC**.
- Datetime nội bộ → timezone-aware.
- Input Calendar Write có timezone → chuẩn hóa về UTC trước khi gửi provider.
- Response hiển thị cho người dùng Việt Nam → `Asia/Ho_Chi_Minh` / GMT+7.
- Không lưu giờ địa phương GMT+7 vào database chỉ vì giao diện đang ở Việt Nam.

Utility dùng chung: `app/core/datetime.py` với `utc_now()`, `to_utc()` và `to_vietnam_time()`.

## 9. Calendar Write V1

Runtime đã được nối đầy đủ theo boundary:

```text
POST /api/v1/agent/chat
  ↓
Calendar classification
  ↓
AccountResolver
  ↓
AuthorizationService(calendar.write)
  ↓ ALLOW
CredentialResolver
  ↓ READY
CalendarToolRegistry
  ↓
GoogleCalendarTool
  ↓
GoogleCalendarAdapter
  ↓
Google Calendar API
```

### Create

Yêu cầu tối thiểu:

- `summary`
- `start`
- `end`

`start` và `end` phải là ISO-8601 có timezone hoặc UTC `Z`. Runtime chuẩn hóa thành UTC trước khi gửi Google.

### Update

- Bắt buộc `event_id`.
- Chỉ patch các field được truyền vào.
- `start`/`end` nếu có sẽ được chuẩn hóa UTC.

### Delete

- Bắt buộc `event_id`.
- Bắt buộc `confirmed=true`.
- Nếu chưa xác nhận → `confirmation_required` và **không gọi provider**.

### Runtime request fields

`POST /api/v1/agent/chat` hỗ trợ thêm:

- `capability`: `calendar.write`
- `action`: `create` | `update` | `delete`
- `event_id`
- `summary`
- `start`
- `end`
- `description`
- `location`
- `confirmed`

Natural-language classification vẫn được giữ cho các câu tiếng Việt thông dụng; với thao tác ghi quan trọng nên gửi `capability/action` và các field resource rõ ràng để tránh suy đoán.

## 10. Safety

Update/delete phải xác định chính xác event.

- 0 candidate → `resource_not_found` ở tầng resource resolution tương lai.
- 1 candidate → có thể tiếp tục authorization/tool.
- >1 candidate → yêu cầu user chọn/xác nhận.
- Delete không được thực hiện nếu thiếu confirmation.

LLM không được gọi Google Calendar trực tiếp và không được bypass Authorization/CredentialResolver.

## 11. Runtime implementation status

### Đã triển khai

- PostgreSQL PermissionRepository + AuthorizationService runtime.
- AccountResolver + PostgreSQL account metadata resolution.
- CredentialResolver + encrypted Google OAuth credential boundary.
- Google OAuth state/PKCE hardening.
- Calendar Tool Registry.
- Google Calendar Tool.
- Google Calendar Adapter CRUD.
- Calendar Read V1 E2E verification.
- Calendar Write V1 runtime orchestration: create/update/delete.
- Delete confirmation gate.
- ISO datetime validation + UTC normalization cho Calendar Write.
- HTTP response UTF-8.

### Chưa đóng acceptance

- E2E Create event với Google Calendar thật — **PASS**.
- E2E Update event với Google Calendar thật — **PASS**.
- E2E Delete event với confirmation — **PASS**.
- Provider error/rollback acceptance — chưa đóng.
- Calendar webhook/push sync — chưa triển khai.

## 12. Calendar Read V1 — Verification Gate CLOSED

Luồng runtime đã được kiểm chứng thực tế:

```text
POST /api/v1/agent/chat
  ↓
Calendar classification
  ↓
AccountResolver
  ↓
AuthorizationService
  ↓
CredentialResolver
  ↓
CalendarToolRegistry
  ↓
GoogleCalendarTool
  ↓
GoogleCalendarAdapter
  ↓
Google Calendar API v3
  ↓
2 event thực tế được trả về
```

Acceptance thực tế đã xác nhận:

- `calendar.read` được phân loại đúng.
- Account Google được resolve đúng.
- Authorization trả `allow`.
- Credential trả `ready`.
- Provider thực sự được gọi (`provider_called=true`).
- Google Calendar API trả event thực tế.
- Tiếng Việt trong HTTP response hiển thị đúng UTF-8.
- Khung ngày đọc theo `Asia/Ho_Chi_Minh` hoạt động đúng.
- Chuẩn UTC của database không bị thay đổi bởi provider boundary.

**Calendar Read V1 được CLOSED.**

## 13. Calendar Write V1 — Verification Gate CLOSED

Calendar Write V1 đã được kiểm chứng E2E trên Google Calendar thật và đủ điều kiện **CLOSED / E2E PASS**.

Acceptance cần đạt:

1. Create tạo đúng event trên Google Calendar — **PASS**.
2. Start/end gửi provider ở UTC nhưng hiển thị lại đúng GMT+7 — **PASS**.
3. Update đúng event theo `event_id` — **PASS**.
4. Delete không gọi provider nếu `confirmed=false` — **PASS**.
5. Delete có `confirmed=true` xóa đúng event — **PASS**.
6. Authorization DENY không gọi provider — chưa E2E trong phase này.
7. Credential thiếu/hết hạn không gọi provider — chưa E2E trong phase này.
8. Provider error trả `provider_error` thay vì làm sập HTTP runtime — chưa E2E trong phase này.

### E2E thực tế đã đóng

- Create: event `p85pvng0r6fmnacg8bfm8lhesg` được tạo thành công.
- Update: chính event trên được đổi thành `Kiểm tra Calendar Update V1`, thời gian `14:00–15:00` GMT+7.
- Delete không xác nhận: trả `confirmation_required`, `provider_called=false`.
- Delete có `confirmed=true`: event `p85pvng0r6fmnacg8bfm8lhesg` được Google Calendar xóa thành công.
- Response `start/end` nhất quán với `Asia/Ho_Chi_Minh` / GMT+7.
- Chuỗi tiếng Việt và UTF-8 được kiểm chứng qua Create/Update.

Không dùng OAuth URL/callback cũ. Không dán access token/refresh token vào request, log hoặc SQL.



## 15. Chuẩn hóa timezone trong response Calendar Write

- Input Calendar Write được chuẩn hóa về UTC trước khi gửi Google Calendar.
- Provider có thể trả event với datetime UTC và `timeZone=UTC`.
- Response API chuyển `start` và `end` sang `Asia/Ho_Chi_Minh` / GMT+7.
- Không thay đổi dữ liệu provider hoặc nguyên tắc lưu UTC trong database.
- Acceptance yêu cầu `dateTime` và `timeZone` trong response phải nhất quán.

## 14. Credential hết hạn nhưng còn refresh token

- CredentialResolver không loại bỏ credential chỉ vì `expires_at` đã qua.
- Credential có `status=active` vẫn được giải mã nếu còn `refresh_token`; Google Auth có thể làm mới access token khi provider được gọi.
- Nếu credential đã hết hạn và không còn `refresh_token`, runtime trả `oauth_required`.
- Đây là trạng thái của access token, không phải trạng thái OAuth account. Không chạy OAuth lại nếu credential active vẫn còn refresh token.


## 16. Calendar Intelligence — Natural Language Date/Time V1

### 16.1 Nguyên tắc

Natural Language Date/Time V1 dùng service Python thuần:

```text
Text người dùng
  ↓
CalendarDateTimeParser
  ↓
datetime timezone-aware
  ↓
Asia/Ho_Chi_Minh
  ↓
UTC tại provider boundary
```

Không dùng Pydantic cho parser V1. Không dùng LangGraph bên trong parser.

### 16.2 Phạm vi V1

Parser hỗ trợ:
- hôm nay;
- ngày mai;
- ngày kia;
- thứ Hai → Chủ nhật;
- tuần sau + thứ;
- ngày `DD/MM` và `DD/MM/YYYY`;
- `9h`, `09:30`, `2h chiều`;
- sáng/trưa/chiều/tối;
- `2 tiếng nữa`, `30 phút nữa`.

Parser yêu cầu reference datetime có timezone nếu caller truyền reference. Không dùng datetime naive.

### 16.3 Ranh giới

Parser không:
- truy cập Google Calendar;
- truy cập credential;
- truy cập authorization;
- chọn account;
- tự quyết định conflict;
- tự tạo/sửa/xóa event.

### 16.4 Runtime status

- Service parser: **đã triển khai**.
- Unit test cho các trường hợp V1: **đã tạo**.
- E2E tích hợp Natural Language vào Calendar Create/Read: **chưa đóng**.
