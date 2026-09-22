# Scheduling Assistant V1

> Đặc tả thiết kế đã được chốt trước khi triển khai code. Tài liệu này là contract cho implementation V1.

## 1. Mục tiêu

Scheduling Assistant V1 cho phép Agent nhận yêu cầu tìm khoảng thời gian phù hợp trong lịch, sử dụng dữ liệu Free/Busy hiện có và trả về các slot có thể sử dụng.

V1 ưu tiên thiết kế rõ boundary và khả năng mở rộng hơn việc đưa business logic vào LangGraph.

## 2. Kiến trúc

```text
USER / API
    ↓
LANGGRAPH SUPER-GRAPH
    ↓
SCHEDULING GRAPH
    ├── classify_request
    ├── resolve_calendar
    ├── get_free_busy
    ├── find_available_slots
    ├── confirm
    └── format_result
    ↓
SCHEDULING SERVICE
    ↓
CALENDAR FREE/BUSY
    ↓
CALENDAR TOOL
    ↓
GOOGLE CALENDAR ADAPTER
    ↓
GOOGLE CALENDAR API
```

Nguyên tắc bắt buộc:

- LangGraph điều phối, không chứa business logic scheduling.
- SchedulingService thực thi thuật toán tìm slot.
- Tool là boundary giữa orchestration/application và capability.
- Provider Adapter là boundary với Google API.
- Authorization và CredentialResolver giữ nguyên boundary hiện tại.
- LLM không quyết định identity, account hoặc permission.

## 3. Graph State V1

State dự kiến gồm:

| Trường | Mục đích |
|---|---|
| request_context | Nội dung yêu cầu và metadata |
| user/session/device | Runtime context |
| intent/action | Intent và action đã phân loại |
| timezone | Múi giờ xử lý |
| search_start | Bắt đầu khoảng tìm kiếm |
| search_end | Kết thúc khoảng tìm kiếm |
| duration_minutes | Thời lượng slot cần tìm |
| calendar_ids | Calendar đã được resolve và authorize |
| authorization | Kết quả authorization |
| busy_periods | Các khoảng bận |
| available_slots | Các slot rảnh |
| conflicts | Conflict nếu có |
| confirmation | Trạng thái xác nhận nếu phase có side effect |
| execution/error | Metadata thực thi và lỗi |

State không chứa credential secret.

## 4. Graph Nodes

### 4.1 classify_request

Xác định yêu cầu có phải scheduling hay không và chuẩn hóa action cần thực hiện.

Không quyết định:
- user identity;
- account permission;
- authorization.

### 4.2 resolve_calendar

Resolve candidate calendar/account metadata theo context hiện tại.

Authorization vẫn do Application layer thực hiện.

### 4.3 get_free_busy

Gọi capability Free/Busy hiện có qua Tool boundary.

Không gọi Google Calendar API trực tiếp từ Graph node.

### 4.4 find_available_slots

Gọi SchedulingService.

Input:
- search window;
- duration;
- busy periods;
- timezone.

Output:
- available slots;
- conflicts nếu có.

### 4.5 confirm

V1 chỉ chuẩn bị boundary cho phase có side effect. V1 hiện tại không tạo/sửa/xóa event nên không yêu cầu confirmation để trả slot.

### 4.6 format_result

Chuyển kết quả domain thành response cho API/user.

## 5. SchedulingService

SchedulingService là Python domain service độc lập.

Không phụ thuộc:

- LangGraph;
- Google Calendar SDK;
- PostgreSQL;
- Qdrant;
- credential storage.

Chức năng chính:

1. nhận search window;
2. nhận duration;
3. nhận busy periods;
4. chuẩn hóa và sắp xếp busy periods;
5. tìm các khoảng trống đủ duration;
6. trả available slots theo timezone contract.

Thuật toán phải deterministic và có unit test độc lập.

## 6. Free/Busy integration

Scheduling Assistant tái sử dụng capability đã CLOSED:

`calendar.read` + `free_busy`

Không tạo permission mới và không thay đổi OAuth scope chỉ để phục vụ Scheduling V1.

## 7. Authorization

Luồng bắt buộc:

```text
AgentContext
  ↓
candidate account
  ↓
Authorization
  ↓ ALLOW
CredentialResolver
  ↓
ToolResolver
  ↓
Calendar Free/Busy
```

Không lấy credential secret trước ALLOW.

## 8. Pydantic

V1 không mặc định sử dụng Pydantic.

Chỉ thêm Pydantic nếu implementation chứng minh một boundary mới cần:
- validation phức tạp;
- normalization;
- serialization;
- stable Tool/Graph contract.

Khi phát sinh nhu cầu đó phải trình bày và chờ chủ project chốt trước khi triển khai.

## 9. Database

V1 không tạo migration chỉ để lưu Graph execution state hoặc available slots tạm thời.

Nếu sau này cần lưu:
- scheduling preferences;
- recurring availability;
- user-defined working hours;
- persisted scheduling rules;

thì thiết kế database riêng trước khi migration.

## 10. Side Effect

V1 **read-only**.

Không:
- create event;
- update event;
- delete event.

Nếu phase sau thêm thao tác ghi Calendar:

```text
Scheduling
  ↓
proposed slot
  ↓
explicit confirmation
  ↓
Calendar Write
  ↓
Google Calendar
```

Phải giữ nguyên confirmation policy hiện hành.

## 11. Multi-calendar / Multi-account

V1 chuẩn bị state cho nhiều calendar nhưng chưa mở rộng policy multi-account.

Nếu có nhiều account cùng provider và request không xác định account, không để LLM tự đoán. Runtime phải áp dụng policy default hiện có hoặc yêu cầu user chọn.

## 12. Testing strategy

### Unit

- tìm slot trong lịch hoàn toàn rảnh;
- slot trước busy;
- slot sau busy;
- nhiều busy periods;
- busy chạm boundary;
- busy bao phủ toàn bộ search window;
- duration không hợp lệ;
- search window không hợp lệ;
- timezone-aware requirement.

### Integration

- Scheduling Graph gọi đúng Free/Busy capability;
- Authorization DENY không gọi provider;
- credential chỉ được resolve sau ALLOW;
- provider response được chuyển đúng vào SchedulingService.

### E2E

Dùng Google Calendar thật với event test:

1. tạo event test;
2. request tìm slot;
3. xác nhận slot conflict/free;
4. kiểm tra response timezone;
5. xóa event test.

Không đánh dấu PASS nếu chưa runtime verification.

## 13. Acceptance Gate

Scheduling Assistant V1 chỉ được đánh dấu CLOSED khi:

- Graph runtime hoạt động;
- SchedulingService unit tests PASS;
- Authorization boundary PASS;
- Free/Busy integration PASS;
- Google Calendar E2E PASS;
- không có credential leak;
- regression Calendar CRUD/Natural Language/FreeBusy vẫn PASS;
- test event được cleanup.

## 14. Không triển khai trong tài liệu này

Tài liệu chưa triển khai:

- recurrence;
- multi-account scheduling policy đầy đủ;
- user working hours persistence;
- automatic event creation;
- optimization theo sở thích người tham dự;
- timezone negotiation phức tạp;
- notification/reminder orchestration.
