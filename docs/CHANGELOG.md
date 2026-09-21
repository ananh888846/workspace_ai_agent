## 2026-09-21 09:20:00 +07:00

### Migration 041–045 DDL design

- Thêm [`docs/MIGRATION_041_045_DDL.md`](./MIGRATION_041_045_DDL.md).
- Thiết kế Automation Trigger, Automation Action, Anomaly, Anomaly Evidence và Audit Log.
- Khóa tenant integrity cho Anomaly/Evidence và audit security boundary.
- Chốt polymorphic Evidence phải có DB-level implementation strategy trước production SQL.
- Chốt Audit Log append-only trong normal runtime và không chứa credential/secret.
- Ghi nhận các implementation gate còn mở: Agent ↔ Organization binding và Evidence source constraint strategy.
- Chưa tạo SQL migration production, chưa tạo database thật và chưa thay đổi application/runtime code.

## 2026-09-21 09:10:00 +07:00

### Migration 031–040 DDL design

- Thêm [`docs/MIGRATION_031_040_DDL.md`](./MIGRATION_031_040_DDL.md).
- Thiết kế Agent, Agent Capability, Tool, Tool Capability, Agent Run, Tool Run, Agent Task, Agent Permission, Agent Message và Automation.
- Bổ sung acceptance tests cho runtime trace, lifecycle, authorization boundary và cross-organization A2A.
- Chốt implementation gate: Agent hiện là global entity nên cần DB-level Agent ↔ Organization binding trước production SQL cho A2A/Agent Task tenant integrity.
- Chưa tạo SQL migration production, chưa tạo database thật và chưa thay đổi application/runtime code.

## 2026-09-21 09:08:00 +07:00

### CHANGELOG file-link rule locked

- Chốt Decision 028: mọi file được thêm/thay đổi và được ghi trong CHANGELOG phải có Markdown link trực tiếp tới file trong repository.
- Từ các entry mới, không ghi tên file dạng plain text nếu có thể gắn link nội bộ.
- Thêm [`docs/DECISIONS.md`](./DECISIONS.md) Decision 028 để làm nguyên tắc lâu dài.

## 2026-09-21 09:02:00 +07:00

### Migration 021–030 DDL design

- Thêm `docs/MIGRATION_021_030_DDL.md`.
- Thiết kế Observation, Event, Activity Session, Activity, Task, Conversation, Message, Memory, Knowledge Document và Knowledge Chunk.
- Khóa tenant integrity cho Event/Activity và authorization boundary của Knowledge.
- Xác định SQL là source of truth cho Knowledge metadata/authorization, Qdrant chỉ là retrieval store.
- Bổ sung acceptance tests cho lifecycle, temporal checks, cross-tenant references và Qdrant authorization.
- Giữ Task schema ở mức contract, không tự phát sinh column ngoài source-of-truth trước khi viết SQL.
- Chưa tạo SQL migration production, chưa tạo database thật và chưa thay đổi application/runtime code.

## 2026-09-21 08:52:00 +07:00

### Migration 011–020 DDL design

- Thêm `docs/MIGRATION_011_020_DDL.md`.
- Thiết kế chi tiết Resources, Resource Permissions, Data Package, Package Versions/Resources/Grants, Devices, User Sessions, Device Users và Device Capabilities.
- Khóa composite tenant integrity cho Resource hierarchy, Data Package, Package Resource/Grant và Device → Resource.
- Bổ sung acceptance tests cho cross-organization insertion, resource/account consistency, session integrity và device capability mapping.
- Chưa tạo SQL migration production, chưa tạo database thật và chưa thay đổi application/runtime code.

## 2026-09-21 08:45:00 +07:00

### Migration 001–010 DDL design

- Thêm `docs/MIGRATION_001_010_DDL.md`.
- Thiết kế chi tiết DDL cho Organizations, Users, Organization Members, External Accounts, Credentials, Roles, Permissions, User Roles, Role Permissions và Account Grants.
- Khóa composite tenant FK cho Account Grant và ownership FK của external account.
- Khóa UNIQUE target keys, delete policy, temporal CHECK, index contract và acceptance tests.
- Chưa tạo SQL migration production, chưa tạo database thật và chưa thay đổi application/runtime code.

## 2026-09-21 08:35:52 +07:00

### V2.1 tenant isolation hardening

- Chốt `account_grants` là tenant-scoped: thêm `organization_id` và yêu cầu owner/grantee cùng thuộc organization.
- Chốt Data Package là tenant-scoped: `data_packages`, versions, package resources và package grants mang `organization_id`.
- Siết `resources.organization_id` và `devices.organization_id` thành bắt buộc.
- Bổ sung composite tenant integrity rules cho Account Grant và Data Package.
- Đồng bộ `DATABASE_V2_DETAILED.md`, `DATABASE.md`, `ERD_V2.md`, `MIGRATION_CONTRACT_V2.md`, `ARCHITECTURE.md` và `DECISIONS.md`.
- Sửa numbering trong `ARCHITECTURE.md`.
- Chưa tạo migration/database/runtime code.

## 2026-09-21 — Migration Contract V2.1 locked

- Thêm `docs/MIGRATION_CONTRACT_V2.md` làm contract chính thức trước migration implementation.
- Khóa PostgreSQL/UUIDv7/TIMESTAMPTZ/JSONB convention, FK/delete policy, composite tenant integrity, UNIQUE/CHECK/INDEX, transaction, seed và rollback policy.
- Khóa migration dependency order 001 → 045.
- Sửa dependency order trong `docs/DATABASE_V2_DETAILED.md`: `resources` phải tồn tại trước `devices`; `devices` phải tồn tại trước `user_sessions`.
- Chưa tạo migration files, chưa tạo database thật và chưa thay đổi application/runtime code.

## 2026-09-21 08:16:10 +07:00

### Final V2.1 documentation consistency fixes

- Sửa section numbering trong `docs/SOURCE_TREE_V2.md`.
- Đồng bộ `organization_members` trong `docs/DATABASE.md` với schema source of truth: `member_role`, composite membership key và `joined_at`.
- Sửa migration order trong `docs/DATABASE_V2_DETAILED.md`: `users` phải được tạo trước `organization_members` để thỏa FK dependency.
- Giữ nguyên migration gate; chưa tạo migration hoặc application runtime code.


## 2026-09-21 08:14:24 +07:00

### Documentation V2.1 synchronization and architecture cleanup

- Sửa `docs/SOURCE_TREE_V2.md`: loại thư mục capability bị lặp và tách rõ Organization Membership khỏi application Authorization Role.
- Chuẩn hóa `docs/ROADMAP_V2.md`: loại Phase 1/Phase 8/Phase 9 bị lặp, khóa lại thứ tự Phase 0 → Phase 10 và migration gate.
- Rút `docs/DATABASE.md` về vai trò overview/domain map; xóa định nghĩa `activities` bị trùng.
- Khóa `docs/DATABASE_V2_DETAILED.md` là schema source of truth.
- Đồng bộ `docs/ARCHITECTURE.md` và `docs/CORE_CONTRACTS_V2.md` về tenant membership, application roles và execution boundary.
- Thêm `docs/ERD_V2.md` cho relationship/authorization flow.
- Thêm `docs/SYNC_INGESTION.md` cho webhook → sync event → worker → provider fetch → knowledge ingestion → Qdrant.
- Thêm Decision 019–022 về membership/authorization, schema source of truth, authorized vector retrieval và webhook ingestion boundary.
- Chỉ thay đổi documentation/architecture contract; chưa tạo migration, database thật hoặc application runtime code.

## 2026-09-21 — V2.1 documentation synchronization

Đồng bộ các tài liệu còn lệch sau đợt mở rộng Architecture V2.1.

### Updated

- `docs/DATABASE.md` → nâng thành DATABASE V2.1, bổ sung Organization/Tenant, resource hierarchy, device binding, Activity Session, Task/Work Order, Agent-to-Agent và Anomaly/Evidence.
- `docs/CORE_CONTRACTS_V2.md` → bổ sung OrganizationContext, tenant isolation, Agent-to-Agent permission, Activity/Task contract và Anomaly evidence contract.
- `docs/SOURCE_TREE_V2.md` → đồng bộ source tree mục tiêu V2.1 với organizations, devices/events, activity_sessions, tasks, agent_communication và anomalies.
- `docs/RUNTIME.md` → bổ sung runtime acceptance tests cho organization isolation, resource hierarchy, device/resource, activity session, task reconciliation, agent permission và anomaly evidence.

### Status

- Chỉ cập nhật documentation/architecture contract.
- Chưa tạo migration, database table hoặc application runtime code.
- V2.1 tiếp tục giữ migration gate: Architecture → Database → ERD → FK/UNIQUE/CHECK → INDEX → Migration Order → Implementation → Runtime Verification.

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


## 2026-09-21 08:05:00 +07:00

### Database V2 Schema Review — Locked

- Bổ sung bảng `role_permissions` vào schema chính thức.
- Enforce ownership của `account_grants` bằng composite FK `(user_account_id, owner_user_id)`.
- Bổ sung kiểm tra nhất quán provider giữa `resources` và `user_accounts`.
- Chốt organization scope: hiện áp dụng rõ cho resources/devices, không dùng membership để bypass authorization.
- Sửa migration order để không trùng số và tôn trọng FK dependencies.
- Cập nhật acceptance checklist và trạng thái schema.
- Chưa tạo migration hoặc application code.


## 2026-09-21 — V2.1 documentation synchronization — Database/ERD/Source Tree/Runtime

### Updated

- Đồng bộ `DATABASE_V2_DETAILED.md` với V2.1: Activity Session, Task/Work Order, Agent-to-Agent Message/Task/Permission và Anomaly/Evidence.
- Bổ sung organization scope và integrity rules cho Event/Activity/Task/Agent/Anomaly domains.
- Đồng bộ `ERD_V2.md` với các quan hệ V2.1 còn thiếu.
- Đồng bộ `SOURCE_TREE_V2.md` để mọi V2.1 domain có vị trí rõ trong application/domain/test boundary.
- Đồng bộ `RUNTIME.md` với database integrity gate và tenant isolation.
- Không tạo migration, không tạo bảng thật và không thay đổi application runtime code.


## 2026-09-21 — Final V2.1 docs audit

### Synchronized

- Authorization tenant boundary, Agent-to-Agent authorization và anomaly semantics.
- Event flow: Observation → Event → Activity Session → Activity.
- Device organization/resource binding.
- Decision Log bổ sung các quyết định V2.1 về tenant, Task/Activity, Agent-to-Agent và evidence-based anomaly.
- Database migration numbering và logical relationship summary được kiểm tra lại.
- Không tạo migration hoặc thay đổi application/runtime implementation.

## 2026-09-21 08:37:00 +07:00

### V2.1 migration-ready integrity audit

- Hoàn thiện tenant columns bắt buộc trong `DATABASE_V2_DETAILED.md`: `account_grants`, `data_packages`, `data_package_resources`, `data_package_grants`, `devices`.
- Bổ sung các `UNIQUE(id, organization_id)` cần thiết cho composite tenant FK.
- Khóa explicit composite FK contract cho Account Grant, Data Package, Resource hierarchy và Device → Resource.
- Đồng bộ `MIGRATION_CONTRACT_V2.md` với bộ composite FK V2.1.
- Kiểm tra migration order 001 → 045: không phát hiện dependency cycle trong contract hiện tại.
- Chưa tạo migration SQL/runtime code.


## 2026-09-21 09:35:00 +07:00

### Full Migration 001→045 review and lock

- Thêm Decision 029 trong [docs/DECISIONS.md](./DECISIONS.md).
- Chốt Agent tenant scope và composite Agent FK.
- Chốt Task/Work Order schema trong [docs/MIGRATION_021_030_DDL.md](./MIGRATION_021_030_DDL.md).
- Chốt Anomaly Evidence bằng explicit source FK trong [docs/MIGRATION_041_045_DDL.md](./MIGRATION_041_045_DDL.md).
- Chốt Automation tenant scope.
- Kết luận: Migration 001→045 đủ design contract để chuyển sang production SQL; chưa tạo SQL/database/runtime.
