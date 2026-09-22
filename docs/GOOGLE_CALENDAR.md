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

### 16.4 Tích hợp Calendar Write

Khi Calendar Write nhận request không truyền `start`, runtime sẽ thử phân tích `payload.message` bằng `CalendarDateTimeParser`.

Luồng:

```text
POST /api/v1/agent/chat
  ↓
Calendar classification
  ↓
AccountResolver
  ↓
Authorization
  ↓
CredentialResolver
  ↓
CalendarDateTimeParser
  ↓
start = datetime timezone-aware Asia/Ho_Chi_Minh
  ↓
Calendar Write
  ↓
UTC tại provider boundary
  ↓
Google Calendar API
```

Nguyên tắc an toàn:

- `payload.start` tường minh luôn được ưu tiên.
- Chỉ thử parse message khi có dấu hiệu ngày/giờ.
- Nếu parser không parse được, `start` vẫn rỗng và Calendar Write trả validation error thay vì tự đoán.
- V1 chỉ tự chuẩn hóa `start`; `end` vẫn phải truyền rõ bằng ISO-8601 có timezone.
- Parser không truy cập account, authorization, credential hoặc provider.

### 16.5 Runtime status

- Service parser: **đã triển khai**.
- Unit test parser V1: **PASS — 9/9**.
- Integration helper cho Calendar Write: **đã triển khai**.
- Integration test helper: **PASS — 4/4**.
- Combined parser + integration tests: **PASS — 13/13**.
- E2E Natural Language Create với Google Calendar thật: **PASS**.
- E2E Natural Language Update với Google Calendar thật: **PASS**.
- Delete safety (`confirmed=false`): **PASS**, `provider_called=false`.
- Delete thật (`confirmed=true`): **PASS**, Google Calendar xóa event thành công.
- **Calendar Natural Language Date/Time V1 — CLOSED / E2E PASS.**

### 16.6 E2E verification thực tế — Natural Language Date/Time V1

E2E được kiểm thử trên Google Calendar thật bằng account `ananh888846@gmail.com`.

#### Create

Request: `Tạo lịch họp ngày 24/09/2026 lúc 09:00`.

- `natural_language_datetime.status = resolved`.
- `start = 2026-09-24T09:00:00+07:00`.
- `timezone = Asia/Ho_Chi_Minh`.
- Google Calendar tạo event thật `vet0dr4i57cobksqmbpgol2jb4`.
- Event `09:00–10:00` GMT+7, trạng thái `confirmed`.

#### Update

Request: `Cập nhật lịch E2E ngày 24/09/2026 lúc 14:00`.

- `natural_language_datetime.status = resolved`.
- `start = 2026-09-24T14:00:00+07:00`.
- Cùng event `vet0dr4i57cobksqmbpgol2jb4` được cập nhật thành `14:00–15:00` GMT+7.
- UTF-8 tiếng Việt trong summary/description/location được kiểm chứng.

#### Delete safety

Khi `confirmed=false`:

- `calendar.status = confirmation_required`.
- `calendar.provider_called = false`.
- `execution.provider_called = false`.
- Không gọi Google Calendar API.

#### Delete thật

Khi `confirmed=true`:

- `calendar.status = ok`.
- `calendar.action = delete_event`.
- `calendar.event_id = vet0dr4i57cobksqmbpgol2jb4`.
- `calendar.provider_called = true`.
- Google Calendar xóa event thành công.

Event E2E đã được xóa sau khi hoàn tất verification, không để lại dữ liệu test trên Calendar.

### 16.7 Acceptance gate — CLOSED

1. Parse ngày/giờ tiếng Việt — **PASS**.
2. Calendar Create bằng natural language — **PASS**.
3. Calendar Update bằng natural language — **PASS**.
4. Delete safety không confirmation — **PASS**.
5. Delete thật có confirmation — **PASS**.
6. Timezone `Asia/Ho_Chi_Minh` — **PASS**.
7. UTF-8 tiếng Việt — **PASS**.
8. Provider Google Calendar API — **PASS**.

**Calendar Natural Language Date/Time V1 — CLOSED / E2E PASS.**


## 12. Free/Busy và Conflict Detection V1 — CLOSED / E2E PASS

Free/Busy và Conflict Detection V1 dùng capability `calendar.read` với action `free_busy`, không tạo permission mới.

Luồng runtime:

```text
AccountResolver
  ↓
AuthorizationService(calendar.read)
  ↓ ALLOW
CredentialResolver
  ↓ READY
CalendarToolRegistry
  ↓
GoogleCalendarTool
  ↓
GoogleCalendarAdapter
  ↓
Google Calendar API freeBusy.query
  ↓
CalendarConflictDetector
  ↓
FREE / CONFLICT
```

Ranh giới:
- GoogleCalendarAdapter chỉ chuyển đổi request/response của provider.
- CalendarConflictDetector là deterministic Python service; không gọi Google API và không truy cập SQL, Qdrant, credential.
- Free/Busy V1 không dùng LangGraph trong service và không dùng Pydantic.
- Datetime nội bộ timezone-aware; provider boundary dùng UTC.
- OAuth scope hiện tại được giữ nguyên.
- Không tạo migration database cho capability này.
- Ưu tiên Google Calendar API và client library chính thức của Google.

### E2E verification thực tế

Account: `ananh888846@gmail.com`.

1. Create event test — **PASS**: `TEST FreeBusy V1`, ID `10krafu0fd8629bb41hpantv9o`, `14:00–15:00` GMT+7.
2. FreeBusy `13:00–16:00` — **PASS / conflict**, busy `14:00–15:00`.
3. FreeBusy `14:30–15:30` — **PASS / conflict**.
4. Boundary `15:00–16:00` — **PASS / free**.
5. Delete event test — **PASS**, `provider_called=true`.

Quy tắc overlap đã được xác nhận qua E2E: `busy.start < requested_end and busy.end > requested_start`.

### Acceptance gate — CLOSED

- ConflictDetector unit tests: **5/5 PASS**.
- Google Calendar Create test event: **PASS**.
- FreeBusy overlap/conflict detection: **PASS**.
- Boundary no-overlap: **PASS**.
- Google Calendar Delete test event: **PASS**.
- Timezone `Asia/Ho_Chi_Minh`: **PASS**.
- Official Google Calendar API/client boundary: **PASS**.
- OAuth scope/migration: **không thay đổi / không cần migration**.

**Calendar Free/Busy + Conflict Detection V1 — CLOSED / E2E PASS.**
