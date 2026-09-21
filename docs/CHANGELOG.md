# CHANGELOG

## 2026-09-20 — Architecture V2 documentation reset

Repository đã được làm sạch và khởi tạo lại lớp tài liệu kiến trúc V2.

### Added

- `docs/ARCHITECTURE.md` — Architecture V2 Final blueprint.
- `docs/DATABASE.md` — Database V2 blueprint.
- `docs/AUTHORIZATION.md` — Authorization model.
- `docs/ACCOUNTS.md` — External Account model.
- `docs/DATA_PACKAGES.md` — Data Package / Resource Access model.
- `docs/DEVICES.md` — Device architecture.
- `docs/EVENTS.md` — Observation/Event/Activity model.
- `docs/MEMORY.md` — Memory boundaries.
- `docs/KNOWLEDGE.md` — Knowledge/Qdrant architecture.
- `docs/AGENTS.md` — Agent architecture.
- `docs/TOOLS.md` — Capability/Tool architecture.
- `docs/PROVIDERS.md` — Provider/adapter architecture.
- `docs/AUTOMATION.md` — Event-driven automation plan.
- `docs/ROADMAP_V2.md` — Ordered implementation roadmap.

### Important

Đây là phase **documentation only**. Không có code application/database được tạo trong phase này.

Các quyết định đã chốt được đưa vào blueprint để làm nguồn tham chiếu trước khi bắt đầu implementation.

### Next gate

Trước khi code:

1. Review Architecture V2.
2. Review Database V2.
3. Đối chiếu với yêu cầu thực tế.
4. Chốt schema/migration plan.
5. Sau đó mới triển khai Phase 1.


## 2026-09-21 07:36:00 +07:00

### Finalize Architecture V2 blueprint

- Hoàn thiện request lifecycle và authorization boundary.
- Khóa quy tắc credential chỉ được lấy sau Authorization ALLOW.
- Hoàn thiện database conventions: ID, time, FK, unique, index và metadata.
- Bổ sung Decision Log 001–017.
- Bổ sung Runtime Contract và runtime gate.
- Bổ sung Security V2 cho credential, logging, data isolation và webhook.
- Chưa tạo application code hoặc database migration.


## 2026-09-21 07:40:00 +07:00

### Add Database V2 Detailed schema blueprint

- Thêm `docs/DATABASE_V2_DETAILED.md`.
- Chi tiết PostgreSQL conventions: UUID/UUIDv7, UTC/TIMESTAMPTZ, FK, UNIQUE, INDEX, JSONB và delete policy.
- Định nghĩa chi tiết column/type/default/nullability cho 13 domain database.
- Bổ sung authorization constraints giữa User, Account, Resource và Data Package.
- Bổ sung relationship map và ERD logic.
- Bổ sung index strategy và integrity constraints.
- Bổ sung transaction boundary, credential access boundary và Knowledge authorization.
- Bổ sung migration order 001–035.
- Bổ sung backup/security requirements.
- Bổ sung acceptance checklist và runtime verification cases.
- Chưa tạo migration hoặc database thật.


## 2026-09-21 07:54:00 +07:00

### Review and lock Database V2 authorization integrity

- Bổ sung `role_permissions` để role thực sự ánh xạ tới capability permission.
- Bổ sung liên kết `resources.user_account_id` cho resource thuộc external account.
- Siết unique/index cho resource theo provider + account + type + external ID.
- Làm rõ ràng buộc owner của Account Grant và resource/account binding.
- Sửa migration order để các FK dependency hợp lệ, đặc biệt `user_sessions.device_id`.
- Bổ sung capability/package context vào audit model.
- Bổ sung Decision 018 về Database Authorization Integrity.
- Giữ nguyên trạng thái documentation/design only; chưa tạo migration hoặc application code.


## 2026-09-21 08:02:00 +07:00

### Define Source Tree and Core Contracts V2

- Thêm `docs/SOURCE_TREE_V2.md` làm blueprint cây source chính thức.
- Tách interfaces, application, domain, security, agent, tools, providers và infrastructure.
- Khóa dependency direction để Domain không phụ thuộc provider/database/framework.
- Thêm `docs/CORE_CONTRACTS_V2.md` cho AgentContext, Authentication, Authorization, AccountResolver, CredentialResolver, ResourceAccessChecker, DataPackageResolver, CapabilityRegistry, ToolResolver, ProviderAdapter và AuditService.
- Cập nhật `docs/ROADMAP_V2.md` để Core Contracts là gate trước implementation Phase 1.
- Chưa tạo application code hoặc migration.


## 2026-09-21 — Architecture V2.1 domain extensions

### Added

- Organization / Tenant và Organization Member.
- Resource hierarchy và tenant scope.
- Device ↔ Resource ↔ Organization binding.
- Activity Session.
- Task / Work Order.
- Agent-to-Agent Message / Task / Permission.
- Anomaly Detection và Anomaly Evidence.

### Updated

- Architecture, Database, Agents, Devices, Events và Decision Log đồng bộ V2.1.
- Roadmap thêm V2.1 gate trước migration.

### Important

Đây vẫn là documentation/design phase. Chưa tạo migration, chưa tạo database thật và chưa thay đổi application runtime code.
