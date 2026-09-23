# Workspace AI Agent — ARCHITECTURE DECISIONS V2

> Decision Log là lịch sử quyết định kiến trúc. Không tự ý thay đổi decision đã chốt mà không cập nhật tài liệu.

## Decision 001 — User Account Model
**Status:** Accepted  
user_accounts là mô hình external account chuẩn; một user có nhiều account.

## Decision 002 — Account ≠ Permission
**Status:** Accepted  
Account xác định nguồn tài khoản; Authorization xác định quyền.

## Decision 003 — Account là dependency của Capability
**Status:** Accepted  
Capability không cần account hoạt động bình thường; capability cần account mới gọi AccountResolver.

## Decision 004 — Authorization thuộc Application
**Status:** Accepted  
Identity xác định user; Application Authorization quyết định quyền.

## Decision 005 — Resource Access
**Status:** Accepted  
Resource access được kiểm tra theo request; ownership không đồng nghĩa access.

## Decision 006 — Data Package
**Status:** Accepted  
Data Package là access definition có version và có thể gom nhiều resource.

## Decision 007 — Data Package không chứa Credential
**Status:** Accepted  
Package không chứa OAuth token, API key hoặc device secret.

## Decision 008 — Credential sau Authorization
**Status:** Accepted  
Candidate account có thể được xác định trước authorization; secret chỉ được lấy sau ALLOW.

## Decision 009 — Conversation / Memory / Knowledge / Data Package
**Status:** Accepted  
Bốn domain tách biệt; retrieval không tự động thành memory.

## Decision 010 — Device ≠ User
**Status:** Accepted  
Device có identity/credential/capability riêng.

## Decision 011 — Observation → Event → Activity
**Status:** Accepted  
AI inference không mặc định là fact.

## Decision 012 — LangChain + CrewAI
**Status:** Rejected / Superseded  
Quyết định lịch sử về LangChain + CrewAI bị loại khỏi kiến trúc project. **Project không dùng LangChain và không dùng CrewAI.** Quyết định hiện hành là **chỉ dùng LangGraph cho orchestration** và **Pydantic dùng chọn lọc cho data contract khi thực sự cần**. Không thêm LangChain/CrewAI làm dependency, abstraction layer hoặc runtime framework.

## Decision 013 — Provider Independence
**Status:** Accepted  
Provider-specific behavior nằm ở Provider/Tool layer.

## Decision 014 — Authorization Precedence
**Status:** Accepted  
Capability Permission AND Account Access AND Resource Access AND Package Access nếu áp dụng = ALLOW. Thiếu/DENY điều kiện bắt buộc = DENY.

## Decision 015 — Runtime Gate
**Status:** Accepted  
Runtime verification là gate trước khi mở rộng phase; phải kiểm tra side effect/provider call khi cần.

## Decision 016 — Documentation is Contract
**Status:** Accepted  
Nếu implementation cần phá kiến trúc, phải cập nhật Decision/Architecture/Database/Changelog.

## Decision 017 — Core Database vs Domain Extensions
**Status:** Accepted  
Không tạo trước các bảng domain đặc thù; chỉ thêm khi capability tương ứng được duyệt.

## Decision 018 — Database Authorization Integrity
**Status:** Accepted  
Database V2 phải biểu diễn đầy đủ ba liên kết authorization quan trọng: role → permission qua `role_permissions`, account-backed resource → `user_accounts`, và account grant owner → account bằng constraint/transaction phù hợp. Migration order phải tôn trọng mọi FK dependency.

## Decision 019 — Organization Membership ≠ Application Authorization Role
**Status:** Accepted  
`organization_members.member_role` chỉ mô tả vai trò membership trong tenant. Application authorization dùng `roles`, `permissions`, `role_permissions`, cùng account/resource/package checks. Membership không tự bypass authorization.

## Decision 020 — Database Schema Source of Truth
**Status:** Accepted  
`docs/DATABASE_V2_DETAILED.md` là source of truth cho column, type, nullability, default, FK, UNIQUE, CHECK, INDEX, delete policy và migration order. `DATABASE.md` chỉ là overview; `ERD_V2.md` là relationship view.

## Decision 021 — Authorized Vector Retrieval
**Status:** Accepted  
Knowledge retrieval phải áp dụng authorization context trước/trong Qdrant retrieval. Không retrieve toàn bộ vector store rồi mới lọc quyền.

## Decision 022 — Webhook Does Not Perform Full Ingestion
**Status:** Accepted  
Webhook chỉ xác thực và ghi nhận sync event; worker thực hiện fetch/normalize/version/chunk/embed/index. Không chạy full ingestion trong HTTP webhook request.

## Decision 023 — Organization as Tenant Boundary
**Status:** Accepted  
Organization là tenant/workspace boundary. User có thể thuộc nhiều Organization; membership xác định tenant eligibility nhưng không thay thế application authorization. Resource/device/activity/task/agent-communication/anomaly entities có tenant scope phải được database và runtime enforce cùng organization.

## Decision 024 — Activity Session and Task Separation
**Status:** Accepted  
Task/Work Order là declared/assigned intent. Observation/Event/Activity Session/Activity là recorded/observed state. Activity không tự chứng minh Task hoàn thành nếu thiếu evidence.

## Decision 025 — Agent-to-Agent Same-Organization Delegation
**Status:** Accepted  
Agent Message và Agent Task là transport/work state; Agent Permission mới quyết định delegation. V2.1 chỉ cho Agent-to-Agent delegation trong cùng Organization. Agent B vẫn chịu user/resource/capability authorization.

## Decision 026 — Evidence-Based Anomaly
**Status:** Accepted  
Anomaly là inference về sai lệch dựa trên evidence, không phải kết luận fraud. Mỗi anomaly phải truy ngược được về source facts/events/activities/tasks/devices/resources trong cùng Organization.

## Decision 027 — Account Grant and Data Package Tenant Scope
**Status:** Accepted  
`account_grants` và Data Package là tenant-scoped trong V2.1. Account grant phải có `organization_id` và owner/grantee cùng là member của organization. `data_packages`, versions, package resources và package grants mang cùng `organization_id`; package không được chứa resource hoặc cấp grant ra ngoài organization. `resources.organization_id` và `devices.organization_id` là bắt buộc.

## Decision 028 — CHANGELOG Must Link Changed/Added Files
**Status:** Accepted  
Mỗi entry trong `docs/CHANGELOG.md` khi ghi nhận file được thêm hoặc thay đổi phải gắn Markdown link trực tiếp tới file trong repository. Quy tắc này áp dụng cho mọi thay đổi documentation/code được ghi vào CHANGELOG, để từ changelog có thể mở thẳng file liên quan. Không ghi tên file dạng plain text nếu file có thể được link nội bộ.

## Decision 029 — Database Timestamp UTC
**Status:** Accepted  
Mọi timestamp do Workspace AI Agent lưu trong database phải dùng UTC và timezone-aware tại application boundary. Không lưu GMT+7/giờ địa phương vào database. Khi hiển thị cho người dùng Việt Nam, presentation/application layer chuyển sang `Asia/Ho_Chi_Minh` (GMT+7). Provider có thể có timezone contract riêng nhưng không thay đổi chuẩn lưu trữ UTC của database.

## Decision 030 — Calendar Write Requires Explicit Confirmation for Delete
**Status:** Accepted  
Calendar Write dùng capability `calendar.write` và luôn đi qua AccountResolver → AuthorizationService → CredentialResolver → ToolResolver trước provider. Create/update có resource contract rõ ràng; delete bắt buộc `event_id` và `confirmed=true`. Nếu chưa confirmation thì không được gọi Google Calendar API.

## Decision 031 — LangGraph as Production Agent Orchestrator
**Status:** Accepted  
LangGraph là framework orchestration duy nhất của toàn bộ Workspace AI Agent trong production.

Phạm vi:
- Điều phối graph/node/edge và thứ tự thực thi.
- Quản lý Agent Run state.
- Rẽ nhánh theo classification, authorization, validation, confirmation, tool result và lỗi.
- Hỗ trợ retry/interrupt/resume khi workflow cần.
- Tạo execution trace có thể liên kết Agent Run → Tool Run → Audit.

Ranh giới:
- LangGraph không sở hữu Authorization policy.
- LangGraph không truy cập trực tiếp credential secret.
- LangGraph không truy cập trực tiếp SQL/Qdrant/provider API nếu bỏ qua Application/Tool/Provider boundary.
- Provider-specific business logic vẫn thuộc Provider/Tool layer.
- LLM không được quyết định identity, account hoặc permission.

Migration rule:
- Không rewrite toàn bộ runtime trong một lần.
- Calendar CRUD V1 đang CLOSED/E2E PASS được giữ làm regression baseline.
- Migrate theo từng capability/graph nhỏ và phải kiểm chứng runtime trước khi đóng phase.

## Decision 032 — Pydantic Selective Tool Contracts
**Status:** Accepted  
Pydantic được dùng **chọn lọc** tại các data boundary khi nó tạo giá trị rõ ràng về validation, normalization, serialization hoặc contract ổn định.

Nên dùng khi:
- input phức tạp đến từ LLM/HTTP;
- nhiều field cần validate;
- dữ liệu cần normalize trước provider;
- output Tool cần contract ổn định cho Graph;
- thao tác nhạy cảm cần schema rõ ràng.

Không bắt buộc khi:
- helper nội bộ đơn giản;
- hàm chuyển đổi dữ liệu nhỏ;
- dữ liệu đã được kiểm soát và type rõ ràng;
- việc tạo Model không cải thiện correctness hoặc maintainability.

Ví dụ:
- Calendar Create/Update;
- Gmail Send;
- Smart Home command nhiều tham số;
- Tool output cần contract ổn định.

Pydantic không được dùng để thay thế Authorization, business rules hoặc Provider Adapter.

## Decision 033 — Calendar nâng cấp sau CRUD
**Status:** Accepted  
Calendar được nâng cấp theo thứ tự Natural Language Date/Time → Free/Busy/Conflict Detection → Scheduling Assistant → Recurrence → Multi-account Calendar. Calendar Intelligence giai đoạn đầu dùng service Python thuần; LangGraph chỉ làm Super-Graph ở tầng điều phối tổng thể và sẽ được tích hợp theo từng capability sau.

## Decision 034 — Chủ project phải chốt trước khi dùng LangGraph/Pydantic cho phần mới
**Status:** Accepted  
Trước mỗi lần triển khai một phần mới có quyết định kỹ thuật trực tiếp về việc sử dụng LangGraph hoặc Pydantic, phải hỏi ý kiến chủ project trước.

Quy trình:
1. Xác định yêu cầu và boundary cần giải quyết.
2. Phân tích xem có thực sự cần LangGraph/Pydantic hay không.
3. Nếu có phương án/framework tốt hơn, phải đề xuất và so sánh cho chủ project.
4. Chờ chủ project chốt.
5. Chỉ sau khi được chấp thuận mới triển khai.

Quy tắc này không yêu cầu hỏi cho mọi helper Python nhỏ hoặc thay đổi không liên quan đến quyết định dùng LangGraph/Pydantic.

Mục tiêu là tránh over-engineering, giữ quyền quyết định kiến trúc ở chủ project và bảo đảm framework được dùng đúng chỗ.

## Decision 035 — Calendar Natural Language Date/Time dùng Python thuần
**Status:** Accepted  
Bước Natural Language Date/Time V1 của Calendar không dùng LangGraph và không dùng Pydantic. Parser là service Python độc lập, timezone-aware và chuẩn hóa theo `Asia/Ho_Chi_Minh`.

Nguyên tắc:
- Không gọi provider, SQL, Qdrant hoặc credential từ parser.
- Không để parser quyết định authorization hoặc account.
- Input tối thiểu là text và reference datetime.
- Output là datetime timezone-aware; provider boundary chịu trách nhiệm chuyển UTC.
- Khi phase sau có dữ liệu phức tạp, phải phân tích nhu cầu Pydantic và hỏi chủ project trước khi dùng.
- LangGraph giữ vai trò Super-Graph ở tầng trên cùng; không nhúng LangGraph vào parser chỉ để orchestration một hàm nhỏ.

## Decision 036 — Calendar Natural Language Date/Time V1 E2E baseline
**Status:** Accepted  
Calendar Natural Language Date/Time V1 được giữ làm regression baseline sau khi hoàn tất runtime verification với Google Calendar thật.

Acceptance đã xác nhận:
- Natural Language Create và Update đi qua CalendarDateTimeParser.
- Datetime được resolve thành timezone-aware Asia/Ho_Chi_Minh.
- Provider boundary tiếp tục chịu trách nhiệm chuẩn hóa UTC.
- Delete bắt buộc confirmation; thiếu confirmation không gọi provider.
- Create/Update/Delete thật đã được kiểm chứng với Google Calendar API.
- Event test sau khi verification đã được xóa.

Ranh giới tiếp theo:
- Free/Busy và Conflict Detection là capability kế tiếp, không được suy luận từ Natural Language parser.
- Trước khi dùng LangGraph hoặc Pydantic cho Free/Busy/Conflict Detection phải thực hiện quy trình tại Decision 034.

## Decision 037 — Calendar Free/Busy V1 không dùng Pydantic
**Status:** Accepted  
Free/Busy và Conflict Detection V1 dùng Python type/dataclass cho internal contract. Không thêm Pydantic nếu chưa có nhu cầu rõ ràng về validation, normalization, serialization hoặc contract phức tạp.

- BusyPeriod, Conflict và ConflictResult là domain data structures.
- ConflictDetector là deterministic Python service.
- Nếu contract sau này trở thành Tool/Graph/API boundary phức tạp, phải phân tích lại và hỏi chủ project trước khi thêm Pydantic.

## Decision 038 — Calendar Free/Busy V1 giữ OAuth scope hiện tại
**Status:** Accepted  
Free/Busy V1 tiếp tục sử dụng capability calendar.read và OAuth scope Calendar hiện tại. Không tạo capability/permission mới và không yêu cầu OAuth lại chỉ để triển khai Free/Busy V1.

- Runtime action là free_busy dưới calendar.read.
- Chưa tạo migration DB cho permission mới.
- Nếu sau này cần least-privilege scope riêng cho FreeBusy, phải thiết kế OAuth migration riêng và hỏi chủ project trước.

## Decision 039 — Ưu tiên API/SDK chính thức của Provider
**Status:** Accepted  
Khi tích hợp provider, Workspace AI Agent phải ưu tiên API và thư viện SDK/client chính thức do chính provider phát hành trước khi xem xét thư viện bên thứ ba.

Thứ tự ưu tiên:
1. Official API/SDK của provider.
2. Python standard library hoặc thư viện nền tảng đã có.
3. Thư viện chuyên dụng chính thức của provider.
4. Third-party library chỉ khi có lý do kỹ thuật rõ ràng.

Không thêm dependency bên thứ ba nếu API/SDK chính thức đã đáp ứng yêu cầu.

## Decision 040 — Calendar Free/Busy + Conflict Detection V1 E2E baseline
**Status:** Accepted  
Free/Busy và Conflict Detection V1 được chốt làm regression baseline sau khi runtime verification hoàn tất với Google Calendar thật.

Acceptance đã xác nhận:
- Create event test thành công với Google Calendar thật.
- FreeBusy trả đúng busy interval và ConflictDetector xác định đúng overlap.
- Khoảng bắt đầu đúng thời điểm busy kết thúc được xác định là không conflict.
- Delete event test thành công sau verification.
- Runtime giữ capability `calendar.read` + action `free_busy`, OAuth scope hiện tại và không tạo migration database.
- Free/Busy service không dùng LangGraph nội bộ và không dùng Pydantic.

Ranh giới tiếp theo:
- Scheduling Assistant là capability kế tiếp theo Decision 033.
- Nếu phase sau cần LangGraph hoặc Pydantic ở boundary mới, phải thực hiện quy trình chốt tại Decision 034 trước khi triển khai.

## Decision 041 — Scheduling Assistant V1: LangGraph orchestration + domain service độc lập
**Status:** Accepted

Scheduling Assistant V1 được chốt là capability đầu tiên dùng LangGraph ở tầng orchestration thực tế, theo nguyên tắc:

```text
LangGraph điều phối
        ↓
Domain Service thực thi
        ↓
Tool làm boundary
        ↓
Provider kết nối bên ngoài
```

### Phạm vi V1
- Nhận yêu cầu tìm thời gian phù hợp cho lịch.
- Chuẩn hóa khoảng thời gian cần tìm.
- Resolve calendar/account theo runtime authorization hiện tại.
- Lấy Free/Busy từ capability `calendar.read` + action `free_busy`.
- Tìm các khoảng thời gian còn trống bằng `SchedulingService`.
- Trả các slot phù hợp và thông tin conflict nếu có.
- Chưa tự tạo/sửa/xóa event trong V1.
- Chưa triển khai recurrence hoặc multi-account scheduling.

### LangGraph
Graph chịu trách nhiệm:
- `classify_request`;
- `resolve_calendar`;
- `get_free_busy`;
- `find_available_slots`;
- `confirm` khi phase sau có side effect;
- `format_result`.

Graph state chứa request context, timezone, khoảng thời gian tìm kiếm, calendar/account context, busy periods, available slots, conflict và confirmation state khi cần.

### Domain boundary
`SchedulingService` là Python service độc lập:
- không phụ thuộc LangGraph;
- không truy cập credential;
- không truy cập SQL/Qdrant;
- không gọi Google Calendar API trực tiếp;
- nhận dữ liệu Free/Busy đã được kiểm soát và trả available slots.

### Pydantic
Không mặc định thêm Pydantic cho Scheduling Assistant V1. Chỉ bổ sung nếu một Tool/Graph boundary phát sinh nhu cầu rõ ràng về validation, normalization, serialization hoặc contract ổn định; khi đó phải hỏi chủ project trước theo Decision 034.

### Database
Scheduling Assistant V1 không mặc định tạo migration. Chỉ tạo migration nếu implementation thực tế chứng minh cần persistence mới.

### Regression
Calendar CRUD V1, Natural Language Date/Time V1 và Free/Busy + Conflict Detection V1 tiếp tục là regression baselines.

## Decision 042 — Agent Execution Contract và Error Contract V1
**Status:** Accepted

Workspace AI Agent dùng một execution/result/error contract thống nhất cho các capability sau Calendar V1.

### Execution Contract
Execution phải mô tả tối thiểu:
- `intent`;
- `capability`;
- `action`;
- `account`;
- `authorization`;
- `credential`;
- `provider_called`.

`provider_called` là execution fact và phải phản ánh provider có thực sự được gọi hay chưa.

### Result Contract
Capability result chuẩn gồm:
- `status`;
- `action`;
- `data`;
- `error`;
- `provider_called`.

### Error Contract
Error chuẩn gồm:
- `code` ổn định cho machine processing;
- `message` không chứa secret;
- `retryable`;
- `provider_called`;
- `details` nếu cần.

### Status V1
```text
not_classified
account_not_found
account_selection_required
authorization_denied
oauth_required
validation_error
confirmation_required
provider_error
unsupported_action
ok
```

### Provider boundary
Lỗi xảy ra trước provider call phải có `provider_called=false`. Nếu provider đã được gọi và phát sinh lỗi thì phải dùng `provider_error` với `provider_called=true`.

### Framework và database
Execution Contract V1 dùng Python dataclass/StrEnum, không tạo migration và không thêm LangGraph/Pydantic chỉ để phục vụ contract.

### Migration rule
Calendar V1 tiếp tục là regression baseline. Các capability mới phải tái sử dụng contract này thay vì tạo response shape riêng.


## Decision 043 — Calendar Recurrence V1 dùng RRULE explicit, không thêm framework/migration
**Status:** Accepted

Calendar Recurrence V1 mở rộng Calendar Write hiện tại bằng recurrence rule dạng RFC 5545/Google Calendar RRULE explicit.

Phạm vi V1:
- hỗ trợ FREQ=DAILY|WEEKLY|MONTHLY|YEARLY;
- hỗ trợ INTERVAL dương;
- hỗ trợ một trong COUNT hoặc UNTIL;
- hỗ trợ BYDAY;
- chuẩn hóa lại RRULE trước khi gửi provider;
- recurrence được gửi trong field Google Calendar recurrence khi create/update.

Ranh giới:
- recurrence validation nằm trong app/services/calendar_recurrence.py;
- không để LLM tự tạo recurrence mà bỏ qua validation;
- không dùng LangGraph riêng cho recurrence vì đây là validation/domain transformation nhỏ;
- không dùng Pydantic vì contract hiện tại chưa cần boundary schema phức tạp;
- không tạo migration vì recurrence là thuộc tính của Calendar Event provider, chưa cần persistence riêng trong DB;
- Authorization, Credential, Tool và Provider boundary hiện tại được giữ nguyên.

V1 chưa bao gồm:
- natural-language recurrence parser phức tạp;
- exception dates (EXDATE), recurrence overrides hoặc chỉnh một instance trong series;
- scheduling assistant tự động tạo recurring event;
- multi-account recurrence.


## Decision 044 — Account Resolver + Account Grant V1: chốt contract trước Multi-account
**Status:** Accepted — Design Locked, chưa triển khai runtime

Trước khi bắt đầu Multi-account V1, Account Resolver và Account Grant phải dùng một contract thống nhất.

### 1. ResolvedAccount

Account Resolver trả về metadata account đã resolve, không chứa secret:
- `account`: `ExternalAccount`;
- `access_mode`: `owner` hoặc `grant`;
- `account_grant_id`: nullable;
- `organization_id`;
- không bao giờ chứa access token, refresh token, client secret hoặc encrypted credential.

Credential chỉ được resolve sau Authorization ALLOW.

### 2. Account selection policy

1. Có `account_hint` → match duy nhất thì resolve.
2. Nếu có default-account policy hợp lệ → dùng default.
3. Nếu chỉ có 1 candidate → resolve.
4. Có nhiều candidate mà chưa xác định được account → `account_selection_required`.
5. Không có candidate → `account_not_found`.

LLM không được tự chọn account. Khi selection required thì không Authorization protected account, không Credential Resolver và không Provider call.

### 3. Account Grant scope

`account_grants.scope` chỉ là **giới hạn quyền được ủy quyền trên account**, không phải permission độc lập và không được nâng quyền cho user.

```text
User Capability Permission
AND Organization Membership
AND Account Ownership / Active Grant
AND Grant Lifecycle
AND Grant Scope nếu access_mode=grant
AND Resource Permission nếu request có resource
=
ALLOW
```

V1 canonical scope:
```json
{"capabilities": ["calendar.read", "calendar.write"]}
```

Nếu scope rỗng hoặc không chứa capability đang yêu cầu thì grant không đủ điều kiện. Grant scope không thể cấp capability mà user không có.

### 4. Grant lifecycle

```text
status = active
AND starts_at IS NULL OR starts_at <= now
AND expires_at IS NULL OR expires_at > now
AND revoked_at IS NULL
```

### 5. Owner vs Grant

- `owner`: account.user_id == current user và organization membership hợp lệ.
- `grant`: account thuộc user khác và current user có active grant hợp lệ.
- Owner không cần grant cho account của chính mình.
- Grant không chuyển ownership và không cấp credential trực tiếp cho grantee.

### 6. Test matrix A01–A20

| ID | Scenario | Expected |
|---|---|---|
| A01 | 1 account, không hint | resolved |
| A02 | 2 accounts, không hint | account_selection_required |
| A03 | 2 accounts, hint đúng | resolved |
| A04 | hint không tồn tại | account_not_found |
| A05 | account user khác, không grant | authorization_denied |
| A06 | account user khác, active grant | tiếp tục Authorization |
| A07 | grant expired | authorization_denied |
| A08 | grant revoked | authorization_denied |
| A09 | grant chưa bắt đầu | authorization_denied |
| A10 | grant khác organization | authorization_denied |
| A11 | owner + capability đúng | allow |
| A12 | owner + thiếu capability | authorization_denied |
| A13 | grantee + capability + grant scope đúng | allow |
| A14 | grantee + capability nhưng scope thiếu | authorization_denied |
| A15 | authorization allow nhưng credential thiếu | oauth_required |
| A16 | authorization deny | credential không được resolve |
| A17 | authorization deny | provider không được gọi |
| A18 | selection required | credential không được resolve |
| A19 | nhiều provider account | không có LLM auto-selection |
| A20 | grant active nhưng account disabled | authorization_denied |

### 7. Side-effect assertions

- Authorization DENY → CredentialResolver call count = 0.
- Authorization DENY → Provider call count = 0.
- Selection required → CredentialResolver call count = 0.
- Selection required → Provider call count = 0.
- Account resolution chỉ đọc metadata, không đọc credential secret.

### 8. Known runtime findings trước implementation

Review 2026-09-22 phát hiện:
1. `execute_google_calendar_write()` tham chiếu `recurrence` nhưng signature chưa nhận tham số, trong khi `main.py` đã truyền `recurrence=payload.recurrence`.
2. `main.py` resolve credential vào `credential_result`, sau đó gọi `resolve_google_credential()` lần nữa để dựng execution response, gây duplicate DB/decrypt work.

Hai finding này sẽ được sửa ở implementation phase; Decision 044 không thay đổi code runtime.

 
### Decision 044 — Implementation update 2026-09-22
**Status:** Runtime fix implemented; Multi-account contract remains design-locked.

Đã xử lý hai finding đã ghi ở trên:
1. `execute_google_calendar_write()` nhận `recurrence` đúng với request flow và truyền RRULE đã normalize tới Calendar Tool.
2. Credential được resolve đúng một lần trong `main.py`; kết quả `credential_result` được tái sử dụng để dựng execution contract, không gọi CredentialResolver lần thứ hai.

Test coverage đã bổ sung cho recurrence runtime signature và việc tái sử dụng credential resolution.

 
### Decision 044 — Multi-account implementation phase 1
**Status:** Implemented — core contract + grant-scope enforcement.

Đã triển khai:
- `AccountCandidate` và `ResolvedAccount`.
- Account Resolver trả về `ResolvedAccount` thay vì account metadata thuần.
- Account candidate giữ `access_mode`, `account_grant_id`, `organization_id`, `grant_scope`; không chứa credential secret.
- Account repository đọc grant metadata từ `account_grants`, vẫn không đọc `account_credentials`.
- Authorization nhận `ResolvedAccount` và chỉ áp dụng grant scope khi `access_mode=grant`.
- Grant scope V1 kiểm tra capability hiện tại; không elevate user capability.
- Owner không bị giới hạn bởi grant scope.
- Resolved account nội bộ được truyền xuyên suốt tới Authorization nhưng không serialize thành secret/API response.

### Verification coverage

Đã bổ sung unit coverage cho:
- A01 — single account resolved.
- A02 — multiple accounts require selection.
- A03 — explicit hint path remains repository-selected.
- A04 — no candidate → account_not_found.
- A11 — owner + capability.
- A12 — owner thiếu capability.
- A13 — grantee + capability + grant scope.
- A14 — grantee thiếu grant scope.
- Account repository grant metadata mapping và không truy cập `account_credentials`.

A15–A20 vẫn cần runtime/integration verification với CredentialResolver và Provider side-effect trước khi đóng Multi-account V1.


## Decision 045 — Runtime Architecture V2.2: FastAPI / Agent Runtime / LangGraph Super-Graph
**Status:** Accepted — Phase 1 implemented

### Bối cảnh
Runtime hiện tại đã có FastAPI Agent entry và Scheduling Graph, nhưng /api/v1/agent/chat vẫn là application entry chính; LangGraph mới được dùng thực tế cho Scheduling Assistant. langgraph.json là graph configuration/discovery, chưa phải LangGraph Server production.

### Quyết định đề xuất
Tách runtime thành các boundary rõ ràng:

```text
FastAPI
  ↓
Agent API Adapter
  ↓
Agent Runtime Entry
  ↓
LangGraph Super-Graph
  ↓
Capability Graph / Service
  ↓
Application Authorization + Credential
  ↓
Tool
  ↓
Provider
```

### Nguyên tắc
1. FastAPI chỉ là HTTP transport boundary.
2. Agent Runtime Entry là application entry duy nhất cho Agent Run.
3. LangGraph Super-Graph là orchestration layer cấp Agent.
4. Capability Graph chỉ dùng khi workflow thực sự cần graph/state/control flow.
5. Scheduling Graph tiếp tục là graph chuyên biệt, không phải HTTP entry.
6. Authorization, CredentialResolver và Execution Contract vẫn thuộc Application boundary.
7. LangGraph không truy cập SQL, Qdrant, credential secret hoặc provider API trực tiếp.
8. Không thêm Agent service vào Docker Compose ở phase kiến trúc này.
9. Không xem langgraph.json là bằng chứng LangGraph Server production.
10. Migration runtime phải incremental; giữ compatibility endpoint và regression baseline.
11. Deployment container/LangGraph Server là decision riêng sau khi Super-Graph runtime ổn định.
12. Trước khi triển khai code có ảnh hưởng trực tiếp tới LangGraph/Pydantic, tiếp tục tuân thủ Decision 034.

### Trạng thái phê duyệt
**CHƯA CHỐT.** Decision này chỉ ghi nhận kiến trúc đề xuất; chưa cho phép triển khai code.


### Decision 045 — Implementation Phase 1
**Status:** Implemented — orchestration seam

Đã triển khai:
- `app/agent_runtime/runtime.py` làm Agent Runtime Entry.
- LangGraph Super-Graph gồm `classify_request → execute_route`.
- `/api/v1/agent/chat` delegate vào Agent Runtime nhưng vẫn giữ compatibility contract.
- Application callback tiếp tục sở hữu Account Resolver, Authorization, Credential Resolver, Tool và Provider flow.
- Graph state không chứa credential secret, SQL connection hoặc provider client.
- Không thêm Agent service vào Docker Compose.
- Không tạo migration database.

Migration rule:
- Không rewrite toàn bộ Calendar runtime trong một phase.
- Calendar V1 tiếp tục là regression baseline.
- Phase 2 chỉ mở sau khi Phase 1 unit + regression verification PASS.


## Decision 046 — Runtime V2.2 Phase 2: Capability Routing trong Super-Graph
**Status:** Accepted — Implemented

Super-Graph phải route capability bằng graph node/edge thay vì để một execution callback duy nhất tự quyết định capability.

### Contract
- classify_request tạo intent, capability, action.
- route_request chọn route dựa trên capability đã được application classification xác định.
- Capability handler được inject vào Runtime; Graph không truy cập SQL, Qdrant, credential secret hoặc provider API.
- calendar.read và calendar.write được đăng ký là Calendar routes trong Phase 2.
- default được giữ để bảo toàn compatibility cho request chưa có capability route riêng.
- Không có route phù hợp và không có default → unsupported_action, provider_called=false.

### Migration rule
Phase 2 không rewrite Calendar execution. Calendar V1 tiếp tục là regression baseline. Việc tách handler/application capability boundary sâu hơn sẽ thực hiện ở phase kế tiếp.


## Decision 047 — Runtime V2.2 Phase 3: Calendar Application Handler

**Trạng thái: Accepted — Implemented, chờ verification local**

### Quyết định

Tách orchestration của Calendar capability khỏi `app/main.py` thành:

- `app/application/capabilities/calendar.py` — `CalendarHandler`.

Agent Runtime/LangGraph chỉ chịu trách nhiệm classification + routing + orchestration. CalendarHandler là application boundary cho capability và thực hiện thứ tự:

`Account Resolver → Authorization → Credential Resolver → Calendar execution`.

### Ràng buộc

1. Handler nhận `AgentRuntimeState`, không nhận credential/secret từ Graph state.
2. Authorization phải thành công trước Credential Resolver.
3. Authorization deny hoặc account selection required không được gọi provider.
4. Calendar business logic tiếp tục nằm ở service/tool/provider hiện hữu.
5. Không tạo migration, không đổi OAuth scope, không đổi Docker topology.
6. `POST /api/v1/agent/chat` tiếp tục là compatibility endpoint.
7. Phase 3 không rewrite Calendar V1; chỉ di chuyển application orchestration.
8. FastAPI `main.py` không còn chứa Calendar execution orchestration.

### Lý do

Giảm trách nhiệm của FastAPI entry, tạo capability boundary ổn định để các capability tiếp theo có thể đăng ký Handler riêng mà không phình `main.py`.

### Verification gate

Phải chạy targeted Calendar Handler + Agent Runtime tests và full regression. Chỉ sau khi PASS mới mở Phase 4.


### Decision 047 — Regression fixes after initial Phase 3 verification

Verification local phát hiện:
- test assertion dùng alias `deny` thay vì canonical `authorization_denied` của Execution Contract V1;
- một test API cũ import `_natural_language_calendar_start` từ `app.main` sau khi helper đã được chuyển vào `CalendarHandler`.

Đã sửa test contract và giữ compatibility alias tại `app.main`. Phase 3 vẫn ở trạng thái **chờ verification lại**; chưa được đóng PASS.


## Decision 047 — Regression boundary compatibility after Calendar Handler extraction

**Trạng thái:** Implemented — chờ verification local lại

Sau khi pull Phase 3 và chạy full regression, phát hiện các test runtime cũ vẫn mock symbol tại `app.main` trong khi CalendarHandler đã sở hữu application boundary. Ngoài ra, request thiếu runtime context cần trả HTTP 400 thay vì để ValueError thoát khỏi FastAPI.

Quyết định xử lý:
- Test runtime/API được cập nhật để mock đúng boundary tại `app.application.capabilities.calendar`.
- `CalendarHandler` trả HTTP 400 khi request cần authorization context nhưng thiếu `X-User-ID` hoặc `X-Organization-ID`.
- Không đưa compatibility alias ngược vào `main.py` cho các dependency đã chuyển boundary; test phải phản ánh kiến trúc mới.
- Không thay đổi DB schema, OAuth scope hoặc Docker topology.
- Không thay đổi Execution Contract.

Verification gate vẫn giữ nguyên: targeted tests + full regression phải PASS trước khi đóng Phase 3.


## Decision 047 — OAuth-required provider boundary invariant

**Trạng thái:** Implemented — VERIFIED

Verification local tiếp theo sau Phase 3 regression fix còn 1 failure: khi Credential Resolver trả `oauth_required`, response vẫn bị đánh dấu `provider_called=true` ở credential boundary.

Chốt invariant:
- `oauth_required` là lỗi trước provider;
- Credential Resolver có thể được gọi sau Authorization, nhưng Google Calendar Provider tuyệt đối chưa được gọi;
- `execution.credential.provider_called = false`;
- `execution.provider_called = false`;
- không chạy Calendar execution khi credential chưa ở trạng thái `ready`.

Đã gia cố trực tiếp tại `CalendarHandler` trước khi trả response cho nhánh credential chưa sẵn sàng.

Không thay đổi DB schema, OAuth scope, Docker topology hoặc Execution Contract semantics.


## 2026-09-22 — Hardening lần 2: cô lập credential provider_called cho oauth_required

Local verification sau commit trước vẫn còn 1 failure: `oauth_required` trả `execution.credential.provider_called = true` dù handler đã dừng trước provider. Đã gia cố bằng cách tạo dict credential mới khi nhánh pre-provider kết thúc, tránh mọi alias/reference có thể làm thay đổi cờ `provider_called` sau phép gán.

**Trạng thái:** chờ verification local lại. Chưa đóng Phase 3.


## 2026-09-22 — Root cause OAuth-required test boundary

Xác định nguyên nhân của failure còn lại trong `test_runtime_oauth_required_error_boundary`: helper `_patch_authorized_runtime()` đang mock `app.application.core_runtime.CredentialResolver`, nhưng `CalendarHandler` đã import `CredentialResolver` trực tiếp vào namespace `app.application.capabilities.calendar`. Vì vậy production handler vẫn dùng Resolver thật; test chỉ mock `resolve_google_credential()` nên response có `status=oauth_required` trong khi `credential_result.status` nội bộ vẫn có thể là `ready`, khiến handler tiếp tục dispatch Calendar và propagate `provider_called=true`.

Chốt sửa: test phải patch đúng symbol tại application boundary mà handler thực sự sử dụng: `app.application.capabilities.calendar.CredentialResolver`.

Không thay đổi production semantics; đây là sửa test boundary để phản ánh đúng dependency injection/import boundary hiện tại.

## 2026-09-22 — Phase 3 VERIFIED

Regression local sau khi sửa đúng test dependency boundary:
- targeted Calendar Handler + Agent Runtime: **6 passed**;
- full regression: **97 passed, 0 failed, 2 warnings**.

Kết luận: Calendar Application Handler extraction đã giữ đúng Application Boundary và Execution/Error Contract. Phase 3 được đóng VERIFIED.


## Decision 048 — Phase 4: E2E Agent + Google Calendar real provider

**Trạng thái:** Accepted — Phase 4A implementation started

Phase 4 kiểm chứng toàn bộ request path bằng Google Calendar thật, thay vì chỉ mock provider:

`FastAPI → Agent Runtime → LangGraph Super-Graph → CalendarHandler → Account Resolver → Authorization → Credential Resolver → Calendar Tool → Google Calendar`.

### Phạm vi Phase 4A
- E2E test chạy opt-in, không làm chậm regression mặc định.
- Tạo event thật bằng `calendar.write` thông qua Agent Runtime.
- Đọc event thật bằng `calendar.read` thông qua Agent Runtime.
- Delete phải đi qua hai bước: request chưa confirmation và request đã confirmation.
- Request delete chưa confirmation phải có `provider_called=false` và không gọi Google Calendar.
- Cleanup event test phải được thực hiện sau test để không để lại dữ liệu kiểm thử.
- Không đưa credential/secret vào test payload hoặc Graph state.

### Cấu hình E2E
Các biến môi trường được dùng bởi test:
- `RUN_GOOGLE_CALENDAR_E2E=1` để bật test.
- `WORKSPACE_E2E_USER_ID` là user đã tồn tại trong database.
- `WORKSPACE_E2E_ORGANIZATION_ID` là organization của user.
- `WORKSPACE_E2E_ACCOUNT_HINT` là account Google cụ thể nếu user có nhiều account; có thể bỏ trống khi resolver tự chọn được một account.

### Quy tắc regression
Không bật E2E real-provider trong `python -m pytest -q` mặc định. Phase 4 chỉ được CLOSED sau khi chủ project chạy targeted E2E với credential thật và xác nhận provider side effects đúng.

### Ranh giới tự nhiên ngôn ngữ
Phase 4A kiểm chứng pipeline/provider trước với request tự nhiên ở classification nhưng vẫn cho phép payload có field chuẩn hóa khi cần. Các yêu cầu như “ngày mai”, “tuần này”, “kéo dài 1 tiếng” sẽ được mở thành các test natural-language extraction riêng, không giả định parser hiện tại đã hỗ trợ đầy đủ trước khi kiểm chứng.

### Provider reference
Google Calendar Events API hỗ trợ create/list/delete event; test của project phải đi qua Tool/Provider hiện hữu thay vì gọi Google API trực tiếp trong test.


## Decision 049 — Identity Architecture V1: Principal, Credential, Interaction Session, Evidence
**Status:** Accepted — Design Locked

Workspace AI Agent sử dụng Identity Layer riêng, không đồng nhất Human, Device và Service.

### 1. Principal
V1 gồm:
- Human Principal;
- Device Principal;
- Service Principal.

Device không phải User.

### 2. Credential
Credential là bằng chứng xác thực Principal:
- Human: Password/Passkey/External OAuth;
- Device: Device Key/Certificate;
- Service: server-to-server credential.

Password provider của Human chưa được chốt trong Decision này. Không tạo Web-only credential source để thay thế Agent Identity.

### 3. External Identity
Một Human có thể liên kết nhiều External Identity/External Account, ví dụ Google, Zalo, Facebook và Instagram. External Identity không tạo User mới.

### 4. Edge Device
ESP32/Luckfox là Device Principal và Interaction Endpoint. Device Authentication và Human Authentication là hai trạng thái độc lập.

### 5. Interaction Session
Một Interaction Session liên kết:
- Human nếu xác thực được;
- Device đang tương tác;
- Organization context nếu có;
- authentication method/status;
- request và lifecycle metadata.

Agent không được tin tuyệt đối vào user identity do Edge gửi; phải kiểm tra Device/Human/Organization trust relationship phù hợp.

### 6. Face Recognition
Face Recognition là authentication/identification method, không phải authorization. Nhận diện thành công không tự cấp permission.

### 7. Unknown Person và Evidence
Nếu Edge không xác thực được Human, Edge tạo event/evidence và có thể lưu binary vào NAS/object storage. PostgreSQL chỉ giữ metadata/reference/integrity/ownership/retention context.

Unknown person không được tự suy diễn thành malicious person.

### 8. Agent Decision
Agent/Policy quyết định hành động tiếp theo dựa trên identity context, device context, evidence và authorization.

Agent có thể yêu cầu lấy Evidence từ storage khi workflow thực sự cần; không bắt buộc truyền raw image/video cho mọi event.

### 9. Authorization boundary
Authentication thành công không đồng nghĩa Authorization thành công.

Protected action phải tiếp tục qua Application Authorization và các capability/account/resource/package checks hiện hành. Edge không được bypass authorization.

### 10. Security invariants
- Device Identity ≠ Human Identity.
- Authentication ≠ Authorization.
- LLM không quyết định identity hoặc permission.
- Credential secret không vào prompt/Graph state/audit/response.
- Evidence binary không lưu trực tiếp trong PostgreSQL.
- Evidence access phải qua authorization context.
- Cross-organization device/session/evidence access phải bị chặn.
- Side effect chỉ được thực hiện sau Authorization ALLOW.

### 11. Implementation gate
Decision 049 chỉ khóa architecture/design. Chưa tạo migration, Identity API, Face Recognition runtime, Luckfox/ESP32 runtime hoặc NAS integration. Các implementation phase phải review schema/ERD/tenant integrity trước migration.


## Decision 050 — Local-First / Self-Hosted Agent
**Status:** Accepted — Architectural Invariant

Workspace AI Agent về lâu dài phải có khả năng chạy hoàn toàn trên hạ tầng local/self-hosted.

### Core local
- Agent Runtime;
- PostgreSQL;
- Qdrant;
- local LLM/Ollama;
- Conversation/Memory/Knowledge;
- Authorization;
- local NAS/object storage khi cần;
- local Edge/Home Assistant integration.

### Cloud boundary
Google, Zalo, Facebook, Instagram, cloud LLM và cloud storage chỉ là provider/integration tùy chọn. Cloud không phải source of truth của Identity/Authorization và không phải dependency bắt buộc của Agent Core.

### Data-local
Dữ liệu mặc định được xử lý/lưu local. Chỉ truyền dữ liệu ra external provider khi capability cần và Authorization cho phép.

### Security
- Edge không bypass Agent Authorization.
- LLM không quyết định Identity/Authorization.
- Provider-specific logic nằm trong Provider boundary.
- Local deployment vẫn phải giữ security boundary.

### Deferred
Offline provider queue, HA/local cluster, mTLS toàn hệ thống, offline sync conflict resolution, local/cloud model routing policy và các Identity/Evidence runtime domain chỉ triển khai khi hệ thống mở rộng.

Chi tiết: [docs/LOCAL_FIRST_SELF_HOSTED_V1.md](./LOCAL_FIRST_SELF_HOSTED_V1.md).


## Decision 051 — Guest Access V1 Deferred
**Status:** Deferred — Design gate not yet opened

Guest Access V1 chưa triển khai runtime chính thức ở phase hiện tại.

### Lý do
Guest không được mô hình hóa đơn giản thành một User giả có UUID tạm thời. Khi Knowledge và Resource Authorization hoàn thiện, Guest có thể cần quyền riêng theo:
- loại tài liệu;
- visibility/publication state của Knowledge;
- Organization/resource scope;
- capability/function;
- rate limit và abuse policy;
- session/interaction context.

### Nguyên tắc chốt
1. Không dùng một Agent user hiện có làm Guest.
2. Không dùng Organization hiện có của user/owner làm Guest context chỉ để làm cho request chạy được.
3. Không tạo Guest principal/database record chỉ để bypass Authorization hiện tại.
4. Guest không được tự động có quyền đọc Knowledge chỉ vì endpoint Chat là public.
5. Guest access phải đi qua Authorization policy riêng khi phase này được mở.
6. Knowledge retrieval phải áp dụng access scope trước/trong Qdrant retrieval theo Decision 021.
7. LLM không được quyết định Guest được phép truy cập tài liệu/chức năng nào.

### Web boundary hiện tại
Laravel Web có thể giữ public Chat boundary ở mức route/UI, nhưng phần Guest identity/authorization đang được xem là **provisional** và chưa được coi là runtime đã verified hoặc production-ready.

Không cấu hình AGENT_CHAT_GUEST_ORGANIZATION_ID và không dùng user/organization hiện có làm Guest context cho đến khi Guest Access contract được thiết kế và chốt.

### Gate để mở lại
Guest Access chỉ được mở sau khi có:
- Knowledge visibility/access model;
- Resource/Capability authorization contract cho Guest;
- principal/session model phù hợp;
- acceptance tests chứng minh Guest không truy cập private/user/org-protected data ngoài policy;
- local runtime verification.

Decision này không thay đổi Authentication V1 của Human User và không thay thế Decision 049/050.


## Decision 052 — Web Administrator dùng Human User + Full Authorization
**Status:** Accepted — Design Locked

Web Administrator V1 không tạo một loại Principal đặc biệt và không tạo một User model riêng cho quản trị Web.

### Mô hình chốt

Một Human User bình thường trong Agent Identity sẽ được cấp một Role quản trị có toàn bộ Permission cần thiết cho phạm vi quản trị hệ thống.

```
Human User
   ↓
Role: system_admin
   ↓
All approved system permissions
```

User này vẫn là User bình thường về mặt Identity. Quyền quản trị đến từ Authorization, không đến từ tên, email hoặc một loại User đặc biệt.

### Nguyên tắc

1. Không dùng `Calendar Test User` làm Administrator.
2. Tạo một Agent User riêng cho Administrator.
3. User Administrator vẫn thuộc mô hình Human User thông thường.
4. Quyền quản trị được cấp qua Role/Permission.
5. Không hard-code email Administrator trong Agent Authorization.
6. Không tạo bảng `web_admin_users` hoặc một Identity source riêng cho Web.
7. Laravel Web chỉ ánh xạ `auth_users.agent_user_id` tới Agent User đã tồn tại.
8. Các User khác về sau có thể được cấp Role/Permission khác nhau mà không thay đổi Identity model.
9. Full authorization chỉ áp dụng trong phạm vi Permission đã được định nghĩa; không đồng nghĩa bỏ qua Authorization boundary.
10. LLM không quyết định quyền quản trị.

### Dữ liệu V1 dự kiến

- 01 Agent Human User riêng cho Web Administrator.
- 01 Role quản trị hệ thống, tên đề xuất: `system_admin`.
- Role này được gán các Permission quản trị cần thiết sau khi Permission catalog được review.
- Administrator có Organization membership phù hợp với tenant quản trị.

### Security boundary

```
Browser
  ↓
Laravel Authentication
  ↓
auth_users.agent_user_id
  ↓
Agent Authentication Context
  ↓
Authorization
  ↓
system_admin permissions
```

Không có đường tắt từ Laravel session tới quyền quản trị.

### Phạm vi hiện tại

Decision này chốt **mô hình Identity + Authorization**, chưa tự động cấp mọi Permission hiện có trong database nếu Permission đó chưa được xác định là quyền quản trị hệ thống.

Bước implementation tiếp theo là review Permission catalog hiện tại, xác định bộ Permission hệ thống, sau đó tạo User/Role/Organization data theo cách idempotent.

Không dùng Administrator để thay thế Guest Principal. Guest Access tiếp tục tuân theo Decision 051.

