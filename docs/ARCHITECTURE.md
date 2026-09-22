# Workspace AI Agent — ARCHITECTURE V2 FINAL

> Blueprint kiến trúc chính thức. Đây là nguồn tham chiếu trước khi viết code.

## 1. Quy tắc bất biến

1. Identity xác định ai; Authorization quyết định được làm gì.
2. Account xác định nguồn tài khoản; Account Grant xác định ai được dùng account.
3. Capability mô tả khả năng; Tool là implementation.
4. Agent không truy cập trực tiếp provider API, SQL hoặc Qdrant nếu bỏ qua Application/Authorization.
5. LLM không quyết định identity, account hoặc permission.
6. Device không phải User.
7. Conversation, Memory, Knowledge, Observation, Event, Activity và Data Package là các domain riêng.
8. Credential chỉ được lấy sau khi Authorization ALLOW.
9. Provider-specific logic nằm trong Provider/Tool layer.
10. Muốn đổi kiến trúc phải cập nhật Decision Log.
11. Mọi timestamp lưu trong PostgreSQL phải theo UTC; khi trả dữ liệu cho người dùng/API phải chuyển sang múi giờ hiển thị đã quy định, mặc định GMT+7 (`Asia/Ho_Chi_Minh`).
12. **LangGraph là framework orchestration duy nhất được chốt cho Agent Runtime production của toàn project.**
13. **LangChain và CrewAI không thuộc kiến trúc chuẩn của project và không được dùng cho runtime production.**
14. **Pydantic chỉ được dùng chọn lọc tại các boundary cần validation, normalization, serialization hoặc contract ổn định; không bắt buộc cho mọi Tool hoặc hàm nội bộ.**
15. **Trước khi triển khai bất kỳ phần mới nào cần LangGraph hoặc Pydantic, phải hỏi ý kiến chủ project. Nếu phát hiện phương án/framework tốt hơn, phải đề xuất và chờ chủ project chốt trước khi triển khai.**

## 2. V2.1 — Tenant, Resource, Session, Task và Multi-Agent

V2.1 bổ sung các domain nền tảng mà không thay đổi nguyên tắc Authorization V2.

### 2.1 Organization / Tenant
Organization là boundary của workspace/domain. Một User có thể là member của nhiều Organization.

`organization_members.member_role` chỉ là vai trò membership trong tenant (owner/admin/member/guest). Nó không thay thế `roles`, `permissions` và `role_permissions` của application authorization. Membership không tự cấp quyền đọc/ghi resource hoặc dùng external account.

### 2.2 Resource hierarchy
Resource có thể có quan hệ cha/con. Hierarchy chỉ mô tả cấu trúc, không tự cấp quyền.

### 2.3 Device ↔ Resource ↔ Organization
Device thuộc một Organization và có thể gắn với một Resource cụ thể. Device identity vẫn độc lập với User.

### 2.4 Activity Session
Activity Session gom các Event/Activity liên quan thành một phiên có start/end/duration/status/confidence.

### 2.5 Task / Work Order
Task biểu diễn công việc được giao hoặc yêu cầu nghiệp vụ, có assignee, resource, trạng thái và thời gian. Activity được đối soát với Task để phát hiện mismatch.

### 2.6 Agent-to-Agent Communication
Agent có thể giao task/message cho Agent khác nhưng không bypass AgentContext, Authorization, ToolResolver hoặc Audit.

### 2.7 Anomaly Detection
Anomaly là kết quả phát hiện sai lệch từ facts/events/activities/tasks; không mặc định là kết luận "fraud".

### 2.8 Execution boundary

```text
LLM / Agent
  ↓ intent / plan
LangGraph
  ↓ graph state / routing / control flow
Application
  ↓ authorization
Capability
  ↓
Tool
  ↓
Provider
```

Không có đường đi `LLM → Tool` hoặc `LLM → Credential` bỏ qua graph/application boundaries.

### 2.9 Nguyên tắc V2.1
- Organization là tenant boundary; không dùng User làm tenant thay thế.
- Resource hierarchy không bypass authorization.
- Device không đại diện cho User.
- Activity Session lưu lifecycle của một phiên; Activity vẫn là domain summary.
- Task là declared/assigned intent; Activity là observed/recorded result.
- Anomaly phải có evidence và detection method.
- Agent-to-Agent message/task phải trace được.
- LLM không tự quyết định authorization hoặc kết luận anomaly cuối cùng.

## 3. Request lifecycle

~~~text
Request
 ↓
Authentication
 ↓
AgentContext
 ↓
LangGraph entry
 ↓
Route / Capability
 ↓
Resolve candidate Account nếu cần
 ↓
Authorization
 ├── Capability permission
 ├── Account access
 ├── Resource access
 └── Data Package access nếu áp dụng
 ↓
Resolve Credential
 ↓
OAuth nếu credential chưa sẵn sàng
 ↓
Resolve Tool
 ↓
Pydantic boundary nếu Tool contract cần validation/normalization
 ↓
Execute
 ↓
Agent Run / Tool Run / Audit
 ↓
Response
~~~

AccountResolver trước Authorization chỉ được xác định candidate account/metadata. Không lấy secret trước ALLOW.

## 4. Authorization

Operation protected chỉ được ALLOW khi mọi điều kiện bắt buộc đạt:

~~~text
Capability Permission
AND Account Access
AND Resource Access
AND Package Access nếu áp dụng
=
ALLOW
~~~

Thiếu hoặc DENY một điều kiện bắt buộc thì không gọi provider/tool.

## 5. AgentContext

~~~text
request_id
user_id
session_id
device_id
capability
action
target_account
target_resource
target_package
metadata
~~~

Context không phải nguồn cấp quyền.

## 6. Account và Capability

AccountResolver chỉ resolve account metadata. Account có trạng thái `pending_oauth` vẫn có thể được resolve để đi tiếp tới Authorization; trạng thái này không có nghĩa là đã có credential hợp lệ và không được dùng để bypass CredentialResolver.

~~~text
Capability
 ├── requires_account=false → Tool
 └── requires_account=true
          ↓
      Account Resolver
          ↓
      Authorization
          ↓
          Tool
~~~

Nếu có nhiều account cùng provider mà request không chỉ rõ account, dùng policy default hoặc yêu cầu user chọn. Không để LLM tự đoán.

## 7. Data Package

Data Package là access definition, không phải credential và không bắt buộc là bản sao dữ liệu. Trong V2.1, Package là tenant-scoped; package, version, resource membership và grant không được vượt organization boundary.

~~~text
Data Package
 └── Version
      ├── Resource A
      ├── Resource B
      └── Resource C
             ↓
           Grant → User
~~~

Resource authorization vẫn có hiệu lực.

## 8. Provider

~~~text
Capability
 ↓
Tool Resolver
 ↓
Provider Adapter
 ↓
External API
~~~

Google là provider đầu tiên. Facebook/Meta, Zalo, Telegram, Home Assistant và provider khác triển khai sau Core.

## 9. Device / Event

~~~text
Device
 ↓
Observation
 ↓
Verification / Detection
 ↓
Event
 ↓
Activity
~~~

AI inference không mặc định là fact.

## 10. Knowledge

~~~text
Source
 ↓
Document
 ↓
Normalize
 ↓
Chunk
 ↓
Embedding
 ↓
Qdrant
~~~

SQL giữ metadata, ownership, access, version/checksum và mapping. Retrieval phải chạy trong authorization context.

## 11. Agent Orchestration và Framework

### 11.1 Framework duy nhất

**LangGraph là framework orchestration duy nhất được chốt cho toàn bộ Workspace AI Agent trong production.**

**Không dùng LangChain. Không dùng CrewAI.**

Không thêm LangChain/CrewAI làm dependency, abstraction layer, agent runtime hoặc orchestration framework trong bất kỳ capability nào.

Nếu sau này có framework mới được xem xét, framework đó chỉ được dùng sau khi:
1. đề xuất được trình bày cho chủ project;
2. so sánh với LangGraph và kiến trúc hiện tại;
3. chủ project chấp thuận;
4. Decision Log được cập nhật.

### 11.2 LangGraph chịu trách nhiệm

- điều phối graph/node/edge và thứ tự thực thi;
- quản lý state của Agent Run;
- rẽ nhánh theo kết quả classification, authorization, validation, confirmation và tool execution;
- hỗ trợ retry/error/interrupt/resume khi workflow cần;
- tạo execution trace rõ ràng.

### 11.3 LangGraph không sở hữu

- Authorization policy;
- Credential storage/resolution;
- Provider-specific business logic;
- SQL/Qdrant access trực tiếp;
- quyết định identity/account/permission.

Tool vẫn là boundary hành động; Provider Adapter vẫn là boundary external API.

### 11.4 Pydantic dùng chọn lọc

**Pydantic không phải framework bắt buộc cho mọi Tool.**

Chỉ dùng Pydantic khi một boundary thực sự cần:
- validation;
- normalization;
- serialization/deserialization;
- input/output contract ổn định;
- schema rõ ràng cho dữ liệu đến từ LLM/HTTP;
- bảo vệ thao tác nhạy cảm có nhiều tham số.

Không tạo Pydantic model chỉ để thay thế type hint hoặc làm code dài hơn.

Ví dụ phù hợp:
- Calendar Create/Update input;
- Gmail Send input;
- Smart Home command có nhiều tham số;
- Tool output cần contract ổn định cho Graph.

Ví dụ không cần ép dùng:
- `to_utc(datetime)`;
- hàm normalize text đơn giản;
- helper nội bộ chỉ nhận một kiểu dữ liệu rõ ràng.

### 11.5 Quyền quyết định trước khi dùng LangGraph/Pydantic

**Mỗi lần chuẩn bị triển khai một phần mới mà có lựa chọn kỹ thuật liên quan trực tiếp đến LangGraph hoặc Pydantic, phải hỏi ý kiến chủ project trước.**

Quy trình bắt buộc:

~~~text
Yêu cầu mới
   ↓
Có cần LangGraph/Pydantic không?
   ↓
Nếu CÓ
   ↓
Phân tích phương án
   ↓
Có phương án tốt hơn không?
   ├── Có → đề xuất + so sánh
   └── Không → trình bày phương án đề xuất
   ↓
Chủ project chốt
   ↓
Mới triển khai
~~~

Điều này không có nghĩa mọi thay đổi Python đều phải chờ hỏi; chỉ áp dụng khi quyết định kỹ thuật mới có ảnh hưởng đến việc sử dụng LangGraph/Pydantic.

## 11.6 Calendar Super-Graph và Calendar Service

Calendar được triển khai theo hai tầng:

- **Hiện tại:** Calendar Intelligence dùng service Python thuần, không bắt buộc LangGraph và không dùng Pydantic cho bước Natural Language Date/Time V1.
- **Tương lai:** LangGraph Super-Graph nằm ở tầng trên cùng để điều phối yêu cầu giữa các capability; Calendar Date/Time Parser vẫn là service domain độc lập.
- Parser không được truy cập Google Calendar API, credential hoặc authorization.
- Parser chỉ nhận text + reference datetime và trả kết quả datetime timezone-aware.
- Chuẩn timezone của parser là `Asia/Ho_Chi_Minh`; trước khi ghi/provider boundary phải chuyển về UTC.
- Khi dữ liệu đầu vào/đầu ra của các phase sau trở nên phức tạp, việc dùng Pydantic phải được phân tích và hỏi chủ project trước.

Luồng mục tiêu:

```text
User
 ↓
LangGraph Super-Graph
 ↓
Calendar Capability
 ↓
Calendar Service
 ├── Natural Language Date/Time
 ├── Free/Busy
 ├── Conflict Detection
 ├── Scheduling
 └── Recurrence
 ↓
Authorization / Tool / Provider boundary
 ↓
Google Calendar API
```

## 12. Audit

Operation nhạy cảm phải truy được request_id, user, session/device, capability/action, account, resource/package, tool, result và thời gian. Agent Run/Graph Run và Tool Run nên được liên kết để có thể truy vết toàn bộ execution path.

## 13. Quy tắc ghi chú trong Python

- Tất cả comment, docstring và ghi chú trong file `.py` phải viết bằng **tiếng Việt**.
- Các tên kỹ thuật bắt buộc giữ nguyên như tên biến/hàm, package, class, API, exception, protocol, framework và thuật ngữ chính thức không cần dịch.
- Không viết comment/docstring tiếng Anh mới trong code Python nếu có thể diễn đạt rõ bằng tiếng Việt.
- Khi sửa file Python có comment/docstring tiếng Anh, ưu tiên chuyển phần ghi chú liên quan sang tiếng Việt trong cùng thay đổi.
- Quy tắc này áp dụng cho code mới và các phần code được chỉnh sửa về sau.

## 13.1 Calendar Natural Language Date/Time V1

Bước đầu tiên của Calendar Intelligence dùng Python thuần để giảm phụ thuộc và giữ service nhẹ.

Phạm vi V1:
- hôm nay, ngày mai, ngày kia;
- thứ trong tuần và `tuần sau`;
- ngày dạng `DD/MM` hoặc `DD/MM/YYYY`;
- giờ dạng `9h`, `09:30`, `2h chiều`;
- sáng/trưa/chiều/tối;
- tương đối `2 tiếng nữa`, `30 phút nữa`;
- kết quả luôn timezone-aware theo `Asia/Ho_Chi_Minh`.

Không thuộc V1:
- recurrence;
- free/busy;
- conflict detection;
- tự chọn lịch tối ưu;
- suy đoán mơ hồ thay người dùng.

## 14. Quy tắc thay đổi

Khi phát sinh yêu cầu mới:
1. cập nhật Decision Log;
2. cập nhật Architecture/Database/domain docs;
3. cập nhật Roadmap nếu cần;
4. ghi Changelog;
5. rồi mới triển khai code.

Với thay đổi framework/orchestration cấp toàn project, phải chốt Decision trước khi migrate runtime.

## 15. Google OAuth boundary

Google OAuth thuộc infrastructure/application integration boundary. OAuth state phải gắn với account, user và organization, được ký và có thời hạn. Authorization code chỉ được đổi thành credential trong callback; credential phải được mã hóa trước khi lưu `account_credentials`. Không lưu token plaintext, không đưa secret vào AgentContext/prompt/audit/HTTP response. Sau khi OAuth hoàn tất, runtime quay lại CredentialResolver để kiểm tra readiness trước ToolResolver.

## 16. Quy ước ngày giờ

- PostgreSQL là nguồn lưu trữ thời gian và dùng UTC làm chuẩn thống nhất.
- Tầng persistence phải ghi timestamp theo UTC; không lưu giờ địa phương GMT+7 trong các cột timestamp nghiệp vụ.
- Khi đọc dữ liệu để hiển thị cho người dùng hoặc response API, application/presentation layer chuyển UTC sang `Asia/Ho_Chi_Minh` (GMT+7).
- Provider có thể yêu cầu timezone riêng theo API contract; việc chuyển đổi đó chỉ áp dụng ở provider boundary và không thay đổi chuẩn UTC của database.
- Các thời gian nhận từ người dùng phải được chuẩn hóa về UTC trước khi ghi database.

## 17. Trạng thái

Blueprint V2.1 đã được cập nhật thêm tenant/resource hierarchy, device-resource binding, activity session, task/work order, agent-to-agent communication và anomaly detection.

**Framework decision:** toàn project chỉ dùng **LangGraph + Pydantic theo nhu cầu** cho orchestration/data contracts; **LangChain và CrewAI bị loại khỏi kiến trúc chuẩn**.

**Quyền quyết định:** trước mỗi triển khai mới có ảnh hưởng trực tiếp đến việc dùng LangGraph/Pydantic, phải hỏi ý kiến chủ project; nếu có phương án tốt hơn phải đề xuất để chủ project chốt.

Database V2.1 001 → 050 đã CLOSED; Agent/Knowledge application runtime vẫn chưa triển khai.


## Calendar Free/Busy V1

Free/Busy và Conflict Detection là Calendar Intelligence capability độc lập.

Luồng:
Calendar request
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
Google Calendar API freeBusy.query
  ↓
CalendarConflictDetector

Nguyên tắc:
- Provider adapter chịu trách nhiệm gọi API chính thức của provider và normalize response.
- ConflictDetector là deterministic Python service, không truy cập provider, SQL, Qdrant hoặc credential.
- V1 dùng capability calendar.read + action free_busy.
- V1 không dùng Pydantic và không nhúng LangGraph vào service.
- LangGraph vẫn là Super-Graph ở tầng orchestration tổng thể.
- Không tạo database migration cho Free/Busy V1.
- Ưu tiên API/SDK chính thức của provider trước third-party library.

## Calendar Free/Busy V1 — CLOSED / E2E PASS

Free/Busy và Conflict Detection V1 đã hoàn tất runtime verification với Google Calendar thật.

Acceptance:
- ConflictDetector unit tests: **5/5 PASS**.
- Create event test: **PASS**.
- FreeBusy `13:00–16:00`: **PASS / conflict** với busy `14:00–15:00`.
- FreeBusy `14:30–15:30`: **PASS / conflict**.
- Boundary `15:00–16:00`: **PASS / free**.
- Delete event test: **PASS**.
- Timezone `Asia/Ho_Chi_Minh`: **PASS**.
- Provider thực sự được gọi: **PASS**.
- Không tạo migration và không thay đổi OAuth scope: **PASS**.

Free/Busy tiếp tục là service domain độc lập; LangGraph chỉ là Super-Graph ở tầng orchestration tổng thể và Pydantic không được thêm cho V1.


## Calendar Scheduling Assistant V1 — Architecture Accepted

Scheduling Assistant V1 là capability đầu tiên đưa LangGraph vào orchestration thực tế nhưng giữ domain logic độc lập.

### Luồng mục tiêu

```text
User / API
   ↓
LangGraph Super-Graph
   ↓
Scheduling Graph
   ├── classify_request
   ├── resolve_calendar
   ├── get_free_busy
   ├── find_available_slots
   ├── confirm
   └── format_result
   ↓
SchedulingService
   ↓
Calendar Free/Busy capability
   ↓
Calendar Tool / Provider boundary
   ↓
Google Calendar API
```

### Graph State V1

State tối thiểu:
- request context;
- user/session/device context;
- intent/action;
- timezone;
- requested search window;
- duration cần tìm;
- candidate calendar/account metadata;
- authorization result;
- busy periods;
- available slots;
- conflicts;
- confirmation state;
- execution/error metadata.

### Boundary rules

- LangGraph chỉ điều phối state, node, edge và control flow.
- `SchedulingService` không import LangGraph.
- `SchedulingService` không gọi provider trực tiếp.
- Authorization vẫn thuộc Application layer.
- Credential chỉ được resolve sau Authorization ALLOW.
- Free/Busy tiếp tục dùng capability `calendar.read` + action `free_busy`.
- Provider-specific logic tiếp tục nằm ở Tool/Provider layer.
- Không đưa SQL/Qdrant trực tiếp vào Graph node.
- Không để LLM tự quyết định identity, account hoặc permission.

### V1 không có side effect

Scheduling Assistant V1 chỉ tìm và trả slot. Việc tạo/sửa event sẽ là phase riêng và khi có side effect phải đi qua confirmation policy hiện hành.

### Database

V1 không tạo migration chỉ để lưu scheduling state. Graph state là execution state; persistence mới chỉ được thêm khi có yêu cầu nghiệp vụ rõ ràng.



## 11.7 — Runtime Architecture V2.2 — Agent Runtime + LangGraph Boundary (PROPOSED)

> Trạng thái: **PROPOSED — chưa triển khai code**. Phần này mô tả kiến trúc mục tiêu để chủ project phê duyệt trước khi thực hiện thay đổi runtime.

### Mục tiêu

Tách rõ ba vai trò hiện đang dễ bị trộn lẫn:
1. **FastAPI** là HTTP/API transport boundary.
2. **Agent Runtime/Application** là nơi tạo AgentContext, thực thi Authentication/AccountResolver/Authorization/CredentialResolver và áp dụng Execution Contract.
3. **LangGraph** là orchestration engine của Agent Run, không phải nơi chứa authorization/provider/credential.

### Kiến trúc mục tiêu

```text
Client
  ↓
FastAPI
  ↓
Agent API Adapter
  ↓
Agent Runtime Entry
  ↓
LangGraph Super-Graph
  ├── classify / route
  ├── capability graph
  │    ├── Calendar → Scheduling Graph
  │    ├── Knowledge
  │    ├── Gmail
  │    ├── Smart Home
  │    └── ...
  ↓
Application Boundary
  ├── Account Resolver
  ├── Authorization
  ├── Credential Resolver
  ├── Tool Resolver
  └── Execution Contract / Error Boundary
  ↓
Tool
  ↓
Provider / Infrastructure
```

### Vai trò FastAPI
FastAPI chỉ chịu trách nhiệm HTTP request/response, authentication transport adapter, request parsing, HTTP error/status mapping và gọi Agent Runtime Entry. FastAPI không trở thành nơi điều phối capability theo kiểu if/elif ngày càng lớn.

### Vai trò Agent Runtime Entry
Agent Runtime Entry là application entry duy nhất cho request agent. Nó tạo/chuẩn hóa AgentContext, khởi tạo Agent Run, đưa request vào LangGraph Super-Graph, nhận Graph Result, áp dụng Execution/Error Boundary và trả kết quả cho FastAPI. Nó không chứa provider-specific logic.

### Vai trò LangGraph Super-Graph
Super-Graph là orchestration layer cấp Agent: route capability, kiểm soát thứ tự phase, điều phối confirmation/error/retry/interrupt khi cần và giữ execution state của Agent Run.

Super-Graph không đọc SQL/Qdrant trực tiếp, không lấy OAuth secret, không tự quyết định authorization và không gọi provider API trực tiếp.

### Capability Graph
Mỗi capability phức tạp có thể có graph riêng. Capability đơn giản không bắt buộc có graph riêng và có thể đi qua node/handler/service trong Super-Graph nếu không cần workflow phức tạp.

```text
Agent Super-Graph
   └── Calendar Capability Graph
         └── Scheduling Graph
```

### Scheduling Graph
app/graphs/scheduling.py tiếp tục là graph chuyên biệt của Scheduling Assistant. Nó không trở thành HTTP entry và không sở hữu authorization/provider.

### Tool / Provider
Tool vẫn là action boundary; Provider Adapter vẫn là external API boundary.

```text
Capability
  ↓
Application Authorization
  ↓
Credential Resolver
  ↓
Tool Resolver
  ↓
Tool
  ↓
Provider Adapter
  ↓
External API
```

### Docker / Deployment
- **Không thêm Agent service vào docker-compose.yml ở giai đoạn này.**
- Postgres và Qdrant tiếp tục là infrastructure services.
- FastAPI/Agent Runtime có thể chạy native Python trong development.
- Đóng gói Agent Runtime thành container hoặc dùng LangGraph Server production là một quyết định deployment riêng.
- langgraph.json chỉ là graph configuration/discovery cho LangGraph CLI/Studio; không được xem là bằng chứng LangGraph Server đang chạy production.

### Migration strategy
1. Giữ /api/v1/agent/chat làm HTTP compatibility endpoint.
2. Tạo Agent Runtime Entry độc lập khỏi FastAPI.
3. Đưa routing orchestration cấp Agent vào Super-Graph.
4. Giữ Calendar Scheduling Graph làm capability graph con.
5. Di chuyển từng capability theo phase.
6. Sau mỗi phase chạy regression trước khi đóng.
7. Chỉ sau khi Super-Graph ổn định mới đánh giá deployment container/LangGraph Server.

### Quy tắc side-effect
Mọi side-effect vẫn phải đi qua: Route → Account → Authorization → Credential → Tool → Provider. Super-Graph không được phép rút ngắn chain này.

### Trạng thái
**PROPOSED — chưa triển khai.** Cần chủ project phê duyệt trước khi bắt đầu thay đổi LangGraph/Pydantic/runtime theo Decision 034.
