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
