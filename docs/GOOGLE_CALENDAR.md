# Google Calendar V1 — Capability / Tool Contract

> Trạng thái: **Design locked — chuẩn bị implementation runtime**  
> Provider: Google  
> Capability: `calendar.read`, `calendar.write`  
> Scope: Calendar events CRUD; chưa bao gồm Calendar ACL/settings management.

## 1. Mục tiêu

Cho phép Agent thực hiện các thao tác với Google Calendar thông qua cùng execution boundary của Workspace AI Agent:

- đọc danh sách/sự kiện;
- đọc một sự kiện;
- tạo sự kiện;
- sửa sự kiện;
- xóa sự kiện.

Agent/LLM không gọi Google Calendar API trực tiếp.

## 2. Execution boundary

```text
User Request
  ↓
Authentication
  ↓
OrganizationContext
  ↓
AgentContext
  ↓
Route / Capability
  ↓
AccountResolver
  ↓
Authorization
  ├── calendar.read  (đọc)
  └── calendar.write (tạo/sửa/xóa)
  ↓
CredentialResolver
  ↓
ToolResolver
  ↓
Google Calendar Tool
  ↓
Google Provider Adapter
  ↓
Google Calendar API
```

Nếu Authorization = DENY:

- không resolve credential;
- không gọi Calendar Tool;
- không gọi Google API;
- audit theo policy.

## 3. Account

Google Calendar là account-backed capability.

Một User có thể có nhiều Google account. Request phải:

1. dùng account hint nếu người dùng chỉ rõ;
2. dùng default-account policy nếu đã cấu hình;
3. nếu có nhiều account và không xác định được account, trả `account_selection_required`.

LLM không được tự chọn account chỉ vì tên/email xuất hiện trong dữ liệu không đủ để chứng minh quyền.

## 4. Resource model

Calendar event được biểu diễn bằng resource mapping provider-neutral.

Khuyến nghị:

- `resource_type = google_calendar` cho calendar;
- `resource_type = google_calendar_event` cho event;
- `provider = google`;
- `external_id` là Google Calendar/Calendar Event ID;
- resource account-backed gắn với `user_account_id`.

Resource hierarchy:

```text
Google Account
  └── Google Calendar
       └── Calendar Event
```

Không tạo bảng `google_calendar_events` riêng trong Core Database V2.1 chỉ để chứa provider-specific data.

Provider-specific fields nằm trong provider adapter / metadata theo contract.

## 5. Capability và action

### Read

Capability: `calendar.read`

Actions:

- `list_events`
- `get_event`

### Write

Capability: `calendar.write`

Actions:

- `create_event`
- `update_event`
- `delete_event`

`calendar.write` là capability mutation hiện tại. Không tạo thêm permission database chỉ để tách create/update/delete ở V1; action vẫn phải được ghi vào Agent/Tool/Audit trace.

## 6. Input contract

### List

Tối thiểu:

- `calendar_id` (default `primary` nếu policy cho phép);
- `time_min`;
- `time_max`;
- `query` optional;
- `max_results` optional;
- `account_hint` optional.

### Get

- `calendar_id`;
- `event_id`;
- `account_hint` optional.

### Create

- `calendar_id`;
- `summary`;
- `start`;
- `end`;
- optional: description, location, attendees, reminders, timezone, recurrence;
- `account_hint` optional.

### Update

Bắt buộc:

- `calendar_id`;
- `event_id`.

Các field thay đổi được truyền theo update/patch contract.

Agent phải xác định rõ event mục tiêu trước khi update. Không update chỉ dựa trên tên sự kiện nếu có nhiều candidate.

### Delete

Bắt buộc:

- `calendar_id`;
- `event_id`.

Nếu request ngôn ngữ tự nhiên chỉ mô tả tên/thời gian mà có nhiều event phù hợp, phải yêu cầu xác nhận/chọn event trước khi delete.

## 7. Safety cho mutation

Delete là destructive operation.

Flow:

```text
User request
  ↓
Resolve candidate events
  ↓
Nếu duy nhất một event rõ ràng → tiếp tục
Nếu nhiều event → yêu cầu chọn/xác nhận
  ↓
Authorization calendar.write
  ↓
Credential
  ↓
Delete
  ↓
Audit
```

Không suy diễn event mục tiêu từ fuzzy match khi có nhiều candidate.

Update cũng phải tránh sửa nhầm event. Nếu có nhiều candidate, không tự chọn.

## 8. Provider mapping

Google Calendar adapter chịu trách nhiệm:

- map account → Google credential context;
- map resource → Calendar ID/Event ID;
- map provider request/response → provider-neutral DTO;
- xử lý Google API errors, retry/rate-limit policy;
- không tự authorize;
- không tự lấy credential.

Core/Application không import Google SDK trực tiếp.

## 9. Idempotency / retry

Create event có nguy cơ tạo duplicate khi retry.

V1 phải hỗ trợ execution idempotency ở application/tool-run boundary trước khi triển khai retry tự động.

Delete:

- event không tồn tại có thể được chuẩn hóa thành `resource_not_found` hoặc provider-specific not-found mapping theo error contract;
- không retry vô hạn.

Update:

- ưu tiên patch/update có target event rõ ràng;
- retry chỉ khi provider policy cho phép.

## 10. Audit

Mọi mutation phải trace được tối thiểu:

```text
request_id
organization_id
user_id
account_id
resource_id
calendar_id
event_id
capability
action
result
timestamp
```

Không ghi OAuth token, refresh token hoặc credential vào audit.

## 11. Runtime acceptance

### Read

- authorized owner → Google API được gọi;
- delegated account có grant → ALLOW;
- unauthorized account/resource → DENY;
- DENY → credential không được resolve.

### Create

- valid input + calendar.write → tạo đúng calendar;
- missing permission → DENY;
- account mismatch → DENY;
- retry không tạo duplicate theo idempotency contract.

### Update

- đúng event + calendar.write → cập nhật đúng event;
- nhiều candidate → yêu cầu chọn/xác nhận;
- unauthorized event → DENY;
- provider failure không ghi audit thành success.

### Delete

- đúng event + calendar.write → xóa đúng event;
- nhiều candidate → không tự xóa;
- unauthorized event → DENY;
- DENY không gọi Google API.

### Multi-account

- User có Google Account A/B;
- request chỉ rõ A → dùng A;
- request không rõ và default tồn tại → dùng default;
- request không rõ và nhiều account không có default → `account_selection_required`.

## 12. V1 boundary

V1 tập trung **Calendar Event CRUD**.

Chưa triển khai trong capability này:

- tạo/xóa calendar;
- Calendar ACL/sharing management;
- Calendar settings;
- conference/Meet lifecycle riêng;
- push notification/webhook;
- recurring-event exception management nâng cao;
- batch mutation.

Các phần trên sẽ được mở bằng Decision/contract riêng khi cần.

## 13. Database decision

**Không cần Migration 052 chỉ để hỗ trợ Event CRUD.**

Schema V2.1 hiện có `user_accounts`, `account_credentials`, `account_grants`, `resources`, `resource_permissions`, audit/tool-run context và composite tenant constraints đủ làm boundary cho Google Calendar.

Calendar-specific state không được tạo thành bảng Core riêng nếu chưa có yêu cầu domain cần persistence ngoài resource mapping.

## 14. Implementation order

1. Google Calendar provider client/adapter.
2. Calendar resource mapper.
3. Calendar tool definitions.
4. `calendar.read` tools.
5. `calendar.write` create/update/delete.
6. Authorization integration.
7. Audit/tool-run trace.
8. Unit + authorization tests.
9. Runtime Google test với account thật.
10. Chốt gate trước khi mở Calendar webhook/sync.

