## 2026-09-24 19:24:00 +07:00 — Fix API/runtime tests for server-to-server authentication

- Đồng bộ tests/unit/api/test_chat_api.py và tests/runtime/test_execution_error_boundary_runtime.py với security contract hiện tại: Bearer token hợp lệ, X-Request-Id UUID và identity headers khi runtime cần user/organization context.
- Giữ nguyên production security boundary trong app/api/security.py; không bypass authentication trong test.
- Dùng token giả chỉ trong test process, không ghi secret thật vào repository.
- Không thay đổi database, authorization logic hoặc provider runtime.

## 2026-09-23 13:30:00 +07:00 — Chốt Identity ERD và Local-First/Self-Hosted

- Merge [Identity ERD V1](./IDENTITY_ERD_V1.md) sau review; trạng thái chuyển từ PROPOSED sang **ACCEPTED — DESIGN LOCKED**.
- Cập nhật [docs/IDENTITY_ARCHITECTURE_V1.md](./IDENTITY_ARCHITECTURE_V1.md) để khóa ERD và Local-First invariant.
- Thêm [docs/LOCAL_FIRST_SELF_HOSTED_V1.md](./LOCAL_FIRST_SELF_HOSTED_V1.md) làm architectural invariant cho deployment local/self-hosted.
- Cập nhật [docs/DECISIONS.md](./DECISIONS.md) với Decision 050.
- Xác định cloud provider là optional integration; Agent Core phải hoạt động độc lập Internet cho các capability local.
- Ghi rõ các phần chưa cần thiết (Identity migrations 052–056, device auth runtime, interaction/evidence runtime, NAS runtime, offline queue/HA/mTLS...) là **DEFERRED — triển khai sau khi hệ thống mở rộng**.
- Không thay đổi Agent runtime/database trong phase này.
## 2026-09-23 13:00:00 +07:00 — Identity ERD V1 design

- Thêm [docs/IDENTITY_ERD_V1.md](./IDENTITY_ERD_V1.md) làm thiết kế ERD Identity V1 trước migration.
- Đối chiếu schema hiện tại và xác định reuse: users, organization_members, user_accounts, account_credentials, devices, device_users, user_sessions, account_grants.
- Thiết kế mới: device_credentials, interaction_sessions, authentication_events, evidence, evidence_storage_objects.
- Không tạo bảng principals polymorphic và không tạo external_identities trùng với user_accounts.
- Tách rõ User Session, Interaction Session và Activity Session.
- Khóa logical distinction giữa candidate identity và authenticated identity trong Authentication Event.
- Khóa Evidence/NAS boundary: PostgreSQL chỉ giữ metadata/reference/integrity; binary nằm ngoài PostgreSQL.
- Đề xuất migration plan 052 → 056 sau khi ERD được chốt; chưa tạo migration hoặc runtime.
- Cập nhật [docs/IDENTITY_ARCHITECTURE_V1.md](./IDENTITY_ARCHITECTURE_V1.md) để tham chiếu ERD.
- **Status:** Identity ERD V1 = **PROPOSED — READY FOR REVIEW**.

## 2026-09-23 — Identity Architecture V1 locked

- Thêm [docs/IDENTITY_ARCHITECTURE_V1.md](./IDENTITY_ARCHITECTURE_V1.md) làm contract kiến trúc cho Identity Layer.
- Chốt Principal gồm Human, Device và Service; Device Identity tách khỏi Human Identity.
- Chốt Credential, External Identity, Interaction Session và Edge Authentication là các boundary riêng.
- Chốt ESP32/Luckfox có thể xác thực device, nhận diện Human tại Edge và tạo Interaction Session.
- Chốt trường hợp không xác thực được Human: Edge tạo Evidence, binary lưu tại NAS/object storage, PostgreSQL giữ metadata/reference.
- Chốt Agent/Policy quyết định hành động tiếp theo; Edge không bypass Authorization.
- Chốt LLM không quyết định identity/permission và Authentication không đồng nghĩa Authorization.
- Ghi [Decision 049](./DECISIONS.md) về Identity Architecture V1.
- Chưa tạo migration, Identity API hoặc runtime implementation.
- **Status:** Identity Architecture V1 = **ACCEPTED — DESIGN LOCKED**.

## 2026-09-21 — Documentation V2.1 current-state synchronization

- Đồng bộ trạng thái Database V2.1: Migration 001 → 050 verified trên PostgreSQL 18.6; DBR-001 → DBR-007 CLOSED; RV-001 → RV-014 PASS.
- Chốt Knowledge Systematization Agent là capability Agent đầu tiên; Google trước, sau đó Facebook/TikTok/Instagram.
- Các trạng thái OPEN trong changelog lịch sử giữ nguyên vì phản ánh thời điểm cũ; không đại diện current state.

## 2026-09-21 — Database V2.1 Post-Implementation Review CLOSED

- Đã chạy acceptance [database/tests/acceptance_046_050.sql](../database/tests/acceptance_046_050.sql) trên PostgreSQL 18.6 với `ON_ERROR_STOP=1`.
- Kết quả: **AT-053 → AT-065 PASS (13/13)**; transaction kết thúc bằng **ROLLBACK**.
- Đã chạy runtime catalog verification [database/tests/runtime_catalog_verification_046_050.sql](../database/tests/runtime_catalog_verification_046_050.sql).
- Kết quả: **RV-001 → RV-014 PASS (14/14)**; transaction kết thúc bằng **ROLLBACK**.
- Xác nhận DBR-001 → DBR-007 đã được giải quyết bởi migration hậu V2.1 046 → 050.
- Cập nhật [docs/DATABASE_V2_1_DBR_RESOLUTION.md](./DATABASE_V2_1_DBR_RESOLUTION.md) chuyển gate sang **CLOSED**.
- Cập nhật [docs/DECISIONS.md](./DECISIONS.md) với Decision 043.
- **Status:** Database V2.1 Post-Implementation Review Gate = **CLOSED**.

## 2026-09-21 — Database V2.1 Post-Implementation Review

- Thêm [docs/DATABASE_V2_1_POST_IMPLEMENTATION_REVIEW.md](./DATABASE_V2_1_POST_IMPLEMENTATION_REVIEW.md).
- Đối chiếu static toàn bộ migration 001 → 045 với Database V2.1 contract và acceptance evidence.
- Xác nhận các tenant boundary chính đã được enforce bằng composite FK/constraint.
- Ghi nhận 7 findings cần chốt trước khi tuyên bố Database V2.1 tenant-integrity hoàn toàn CLOSED:
  - DBR-001 Event user ↔ organization.
  - DBR-002 Activity Session user ↔ organization.
  - DBR-003 Activity user ↔ organization.
  - DBR-004 Agent Run ↔ Conversation ownership.
  - DBR-005 Tool Run ↔ external account execution context.
  - DBR-006 Audit Log ↔ external account tenant/user context.
  - DBR-007 Resource uniqueness semantics theo tenant/provider/account.
- Không sửa ngược Migration 001 → 045; mọi schema correction sẽ đi bằng migration hậu V2.1.
- Runtime pg_catalog/information_schema verification chưa được thực hiện trong review này.
- **Status:** Post-Implementation Review = **ACTIONS OPEN**.

## 2026-09-21 08:00:00 +07:00 — Migration 034 → 045 PostgreSQL acceptance verified

- Đã chạy acceptance [database/tests/acceptance_034_045.sql](../database/tests/acceptance_034_045.sql) trên PostgreSQL 18.6 với `ON_ERROR_STOP=1`.
- Kết quả: **AT-041 → AT-052 đều PASS (12/12)**.
- Acceptance transaction kết thúc bằng **ROLLBACK**, nên dữ liệu test không được giữ lại.
- Migration 041 được tạo thành công; các migration 042 → 045 đã tồn tại trong database và không cần chạy lại.
- **Gate:** Migration 034 → 045 đã PASS và được đóng.

## 2026-09-21 — Migration 034 → 045 production SQL created

- Thêm [database/migrations/034_create_tool_capabilities.sql](../database/migrations/034_create_tool_capabilities.sql) → [database/migrations/045_create_audit_logs.sql](../database/migrations/045_create_audit_logs.sql).
- Khóa DB-level tenant integrity cho Agent Run, Agent Task, Agent Permission, Agent Message và Automation.
- Automation Trigger/Action kế thừa tenant scope từ Automation root.
- Anomaly dùng composite tenant references và confidence/time CHECK.
- Anomaly Evidence dùng bảy nullable source FK + exactly-one CHECK; không dùng polymorphic source.
- Audit Log có append-only trigger và secret-key metadata guard.
- Thêm [database/tests/acceptance_034_045.sql](../database/tests/acceptance_034_045.sql) và [database/tests/README_034_045.md](../database/tests/README_034_045.md).
- **Status:** Production SQL đã tạo; PostgreSQL acceptance 034 → 045 chưa chạy. Gate vẫn OPEN.

## 2026-09-21 — Migration 011 → 033 integration acceptance verified

- Đã chạy [database/tests/acceptance_011_033.sql](../database/tests/acceptance_011_033.sql) trên PostgreSQL 18.6 với ON_ERROR_STOP=1.
- Kết quả: **AT-035 → AT-040 đều PASS (6/6)**.
- Đã xác nhận resource/device/session, observation/event/activity/task, conversation/message/memory, knowledge/Qdrant mapping và agent/capability/tool integration hoạt động đúng trong transaction test.
- Đã xác nhận cross-tenant device → resource và task → event bị database reject.
- Acceptance transaction kết thúc bằng **ROLLBACK**, nên dữ liệu test không được giữ lại.
- **Gate:** Migration 011 → 033 integration đã PASS và được đóng.
- Các migration block vẫn giữ verification gate riêng theo contract.

## 2026-09-21 17:20:00 +07:00 — Migration 021 → 030 production SQL created

- Tạo production SQL `database/migrations/021_...sql` → `030_...sql` theo schema lock.
- Tạo `database/tests/acceptance_021_030.sql` với AT-021 → AT-030.
- Tạo `database/tests/README_021_030.md` hướng dẫn chạy.
- Chưa chạy verification thực tế; gate 021 → 030 vẫn OPEN.

## 2026-09-21 17:00:00 +07:00 — Migration 021 → 030 pre-SQL review lock

- Review lại [docs/MIGRATION_021_030_DDL.md](./MIGRATION_021_030_DDL.md) trước khi tạo production SQL.
- Sửa/khóa tenant integrity cho Observation → Event → Activity Session → Activity bằng organization context và composite FK.
- Khóa exact Task/Work Order column list theo V2.1 source of truth.
- Giữ Conversation/Memory theo user ownership; không thêm organization scope ngoài contract.
- Giữ SQL là source of truth cho Knowledge authorization; Qdrant chỉ là retrieval store.
- Chưa tạo production SQL hoặc database cho 021 → 030.

## 2026-09-21 10:20:00 +07:00 — Fix acceptance AT-020 fixture

- Lần chạy acceptance 011 → 020 đầu tiên dừng tại **AT-020** do fixture của test dùng `device_a` cùng organization với session, nên điều kiện cross-organization không thể xảy ra.
- Không phải lỗi production migration 018; đây là lỗi của test fixture.
- Sửa [database/tests/acceptance_011_020.sql](../database/tests/acceptance_011_020.sql): thêm `device_b` thuộc Org B và dùng device này cho AT-020 để kiểm tra đúng session Org A + user Org A + device Org B → **REJECT**.
- Commit sửa test: `77b7fc76d46c418bcb5f22bd1cc70298b554a462`.
- **Status:** Migration 011 → 020 đã chạy `BEGIN → COMMIT`; acceptance AT-011 → AT-022 cần chạy lại sau khi sửa fixture.

## 2026-09-21 10:10:00 +07:00 — Production SQL Migration 011 → 020

- Thêm [database/migrations/011_create_resources.sql](../database/migrations/011_create_resources.sql).
- Thêm [database/migrations/012_create_resource_permissions.sql](../database/migrations/012_create_resource_permissions.sql).
- Thêm [database/migrations/013_create_data_packages.sql](../database/migrations/013_create_data_packages.sql).
- Thêm [database/migrations/014_create_data_package_versions.sql](../database/migrations/014_create_data_package_versions.sql).
- Thêm [database/migrations/015_create_data_package_resources.sql](../database/migrations/015_create_data_package_resources.sql).
- Thêm [database/migrations/016_create_data_package_grants.sql](../database/migrations/016_create_data_package_grants.sql).
- Thêm [database/migrations/017_create_devices.sql](../database/migrations/017_create_devices.sql).
- Thêm [database/migrations/018_create_user_sessions.sql](../database/migrations/018_create_user_sessions.sql).
- Thêm [database/migrations/019_create_device_users.sql](../database/migrations/019_create_device_users.sql).
- Thêm [database/migrations/020_create_device_capabilities.sql](../database/migrations/020_create_device_capabilities.sql).
- Bổ sung database-level resource account ownership/provider consistency bằng composite FK + trigger.
- Bổ sung tenant boundary cho resource permissions, user sessions và device users.
- Thêm [database/tests/acceptance_011_020.sql](../database/tests/acceptance_011_020.sql) với AT-011 → AT-022.
- Thêm [database/tests/README_011_020.md](../database/tests/README_011_020.md).
- **Status:** SQL đã tạo trên GitHub; **chưa chạy** trên PostgreSQL sạch. Chưa đánh dấu PASS.
## 2026-09-21 10:05:00 +07:00 — Migration 011 → 020 resource permission tenant hardening

- Reviewed resource_permissions as an authorization boundary before SQL generation.
- Added organization_id and composite tenant FKs so permission grants cannot cross organization boundaries.
- Added AT-012 for cross-organization resource permission rejection.
- Updated [docs/MIGRATION_011_020_DDL.md](./MIGRATION_011_020_DDL.md), [docs/MIGRATION_CONTRACT_V2.md](./MIGRATION_CONTRACT_V2.md) and [docs/DATABASE_V2_DETAILED.md](./DATABASE_V2_DETAILED.md).
- Gate remains pre-SQL review; production SQL is generated only from the corrected contract.

## 2026-09-21 10:00:00 +07:00 — Migration 011 → 020 pre-SQL integrity correction

- Reviewed [docs/MIGRATION_011_020_DDL.md](./MIGRATION_011_020_DDL.md) before production SQL generation.
- Locked user_sessions.organization_id plus composite tenant FKs for user/device binding.
- Locked tenant-scoped device_users with composite FKs to devices and organization_members.
- Locked resources(user_account_id, owner_user_id) → user_accounts(id, user_id) for account ownership integrity.
- Locked database-level provider/account compatibility for account-backed resources.
- Updated [docs/MIGRATION_CONTRACT_V2.md](./MIGRATION_CONTRACT_V2.md) and [docs/DATABASE_V2_DETAILED.md](./DATABASE_V2_DETAILED.md).
- Gate: review correction complete; SQL 011 → 020 may now be generated from the corrected contract.


## 2026-09-21 08:30:00 +07:00 — Migration 001 → 010 verified on PostgreSQL 18.6

- Đã chạy thực tế [database/migrations/001_create_organizations.sql](../database/migrations/001_create_organizations.sql) → [database/migrations/010_create_account_grants.sql](../database/migrations/010_create_account_grants.sql) trên PostgreSQL 18.6 trong database sạch.
- Đã chạy [database/tests/acceptance_001_010.sql](../database/tests/acceptance_001_010.sql) với `ON_ERROR_STOP=1`.
- Kết quả: **AT-001 → AT-008 đều PASS**.
- Acceptance test kết thúc bằng `ROLLBACK`, nên dữ liệu test không được giữ lại.
- Cập nhật [database/tests/README.md](../database/tests/README.md), [docs/MIGRATIONS_V2_DESIGN.md](./MIGRATIONS_V2_DESIGN.md), [docs/MIGRATION_CONTRACT_V2.md](./MIGRATION_CONTRACT_V2.md), [docs/DATABASE_V2_DETAILED.md](./DATABASE_V2_DETAILED.md) và [docs/DECISIONS.md](./DECISIONS.md) để phản ánh trạng thái đã verify.
- **Gate:** Migration 001 → 010 đã PASS; đủ điều kiện chuyển sang review/implementation Migration 011 → 020.
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

## 2026-09-21 09:45:00 +07:00

### Production SQL Migration 001→010

- Thêm [database/migrations/001_create_organizations.sql](../database/migrations/001_create_organizations.sql).
- Thêm [database/migrations/002_create_users.sql](../database/migrations/002_create_users.sql).
- Thêm [database/migrations/003_create_organization_members.sql](../database/migrations/003_create_organization_members.sql).
- Thêm [database/migrations/004_create_user_accounts.sql](../database/migrations/004_create_user_accounts.sql).
- Thêm [database/migrations/005_create_account_credentials.sql](../database/migrations/005_create_account_credentials.sql).
- Thêm [database/migrations/006_create_roles.sql](../database/migrations/006_create_roles.sql).
- Thêm [database/migrations/007_create_permissions.sql](../database/migrations/007_create_permissions.sql).
- Thêm [database/migrations/008_create_user_roles.sql](../database/migrations/008_create_user_roles.sql).
- Thêm [database/migrations/009_create_role_permissions.sql](../database/migrations/009_create_role_permissions.sql).
- Thêm [database/migrations/010_create_account_grants.sql](../database/migrations/010_create_account_grants.sql).
- Đã triển khai PK/FK/composite tenant FK/UNIQUE/CHECK/index theo thiết kế 001→010.
- Chưa chạy trên PostgreSQL thật trong bước này; bước kế tiếp là clean PostgreSQL acceptance test AT-001→AT-008.

## 2026-09-21 17:00:00 +07:00 — Migration 011 → 020 verified on PostgreSQL 18.6

- Đã chạy thực tế [database/migrations/011_create_resources.sql](../database/migrations/011_create_resources.sql) → [database/migrations/020_create_device_capabilities.sql](../database/migrations/020_create_device_capabilities.sql) trên PostgreSQL 18.6.
- Đã chạy [database/tests/acceptance_011_020.sql](../database/tests/acceptance_011_020.sql) với `ON_ERROR_STOP=1`.
- Kết quả: **AT-011 → AT-022 đều PASS (12/12)**.
- Acceptance transaction kết thúc bằng `ROLLBACK`, nên dữ liệu test không được giữ lại.
- Lỗi fixture AT-020 trước đó đã được sửa bằng cách dùng `device_b` thuộc Org B để kiểm tra session Org A + device Org B.
- **Gate:** Migration 011 → 020 đã PASS; đủ điều kiện chuyển sang review/implementation Migration 021 → 030.


## 2026-09-21 08:00:00 +07:00 — Post-V2.1 DBR decisions and migrations 046–050

### Added

- [database/migrations/046_harden_activity_event_user_tenant_integrity.sql](../database/migrations/046_harden_activity_event_user_tenant_integrity.sql) — same-organization user membership for Event, Activity Session and Activity.
- [database/migrations/047_harden_conversation_owner_integrity.sql](../database/migrations/047_harden_conversation_owner_integrity.sql) — bind Agent Run conversation to the same user.
- [database/migrations/048_bind_tool_run_account_context.sql](../database/migrations/048_bind_tool_run_account_context.sql) — bind Tool Run to execution tenant/user and direct/delegated account context.
- [database/migrations/049_bind_audit_account_context.sql](../database/migrations/049_bind_audit_account_context.sql) — bind Audit Log account context to direct ownership or Account Grant.
- [database/migrations/050_lock_resource_identity_semantics.sql](../database/migrations/050_lock_resource_identity_semantics.sql) — separate account-backed and local resource identity uniqueness.
- [database/tests/acceptance_046_050.sql](../database/tests/acceptance_046_050.sql) — acceptance tests AT-053 → AT-065.
- [database/tests/README_046_050.md](../database/tests/README_046_050.md) — execution guide for the 046 → 050 acceptance gate.

### Updated

- [docs/DECISIONS.md](./DECISIONS.md) — Decision 039 → 042 accepted DBR-005 → DBR-007 and migration set 046 → 050.
- [docs/DATABASE_V2_1_DBR_RESOLUTION.md](./DATABASE_V2_1_DBR_RESOLUTION.md) — DBR-001 → DBR-007 resolved for migration.
- [docs/MIGRATION_CONTRACT_V2.md](./MIGRATION_CONTRACT_V2.md) — post-V2.1 migration contract.
- [docs/DATABASE_V2_DETAILED.md](./DATABASE_V2_DETAILED.md) — Tool Run, Audit Log and Resource identity amendments.
- [docs/ERD_V2.md](./ERD_V2.md) — post-V2.1 integrity relationship amendments.

### Gate

Migration 046 → 050 đã được tạo nhưng **chưa được verify runtime trên PostgreSQL 18.6**. Database V2.1 overall gate vẫn **OPEN** cho đến khi acceptance và catalog verification PASS.


## 2026-09-21 08:30:00 +07:00 — Harden migration preflight and runtime catalog gate

### Updated

- Migrations 046 → 050 now perform preflight validation before replacing/adding constraints or indexes, so existing invalid production data blocks the migration instead of being silently left outside the new integrity contract.
- `database/tests/runtime_catalog_verification_046_050.sql` added to verify required constraints, columns, triggers and resource identity indexes directly from PostgreSQL catalog metadata.
- `database/tests/README_046_050.md` updated with the runtime verification command.

### Gate

Database V2.1 remains **OPEN**. Runtime execution has not been performed in this environment because Docker/PostgreSQL is not available to the current tool runtime.


## 2026-09-24 14:39:00 +07:00 — Multi-Hybrid LLM V1 approved

### Updated

- [docs/DECISIONS.md](./DECISIONS.md) — thêm Decision 054 về Multi-Hybrid LLM V1.
- [docs/CONFIGURATION.md](./CONFIGURATION.md) — sẽ bổ sung cấu hình LLM local/cloud/hybrid trong bước implementation.
- [docs/LOCAL_FIRST_SELF_HOSTED_V1.md](./LOCAL_FIRST_SELF_HOSTED_V1.md) — giữ Ollama/local LLM là mặc định và cloud LLM là optional provider.

### Decision

Chốt triển khai Multi-Hybrid LLM V1 theo mô hình tối giản: `local`, `cloud`, `hybrid`; hybrid fallback **local/Ollama → cloud** khi local provider thất bại. Không tạo migration DB và chưa triển khai intelligent routing/cost/usage/model scoring.

### Gate

Đã hoàn tất documentation decision gate. Bước tiếp theo là implementation LLM provider contract/resolver, sau đó cloud adapter và hybrid fallback; mỗi bước phải chạy regression.


## 2026-09-24 14:41:32 +07:00 — Multi-Hybrid LLM V1 — H1 Provider Contract + Resolver

- Triển khai H1 theo [Decision 054](DECISIONS.md): tạo LLM provider boundary tối thiểu và `LLMResolver` với ba mode `local`, `cloud`, `hybrid`.
- Thêm [`app/llm/providers.py`](../app/llm/providers.py) và [`app/llm/resolver.py`](../app/llm/resolver.py); chưa kết nối provider thật vào Agent Runtime.
- Thêm unit tests tại [`tests/unit/llm/test_resolver.py`](../tests/unit/llm/test_resolver.py).
- Bổ sung cấu hình [`docs/CONFIGURATION.md`](CONFIGURATION.md) và [`.env.example`](../.env.example) cho `LLM_MODE` và cloud provider.
- Không tạo migration/DB table; không thay đổi Authorization, Calendar hoặc LangGraph state contract.
- Verification gate: `python -m pytest tests/unit/llm -q` và `python -m pytest -q`.


## 2026-09-24 14:48:20 +07:00 — Multi-Hybrid LLM V1 — H2 Ollama Provider Adapter

- Thêm Ollama provider adapter tại [`app/llm/ollama.py`](../app/llm/ollama.py).
- Thêm factory [`app/llm/factory.py`](../app/llm/factory.py) để wiring Settings → OllamaProvider → LLMResolver.
- Thêm tests [`tests/unit/llm/test_ollama.py`](../tests/unit/llm/test_ollama.py) và [`tests/unit/llm/test_factory.py`](../tests/unit/llm/test_factory.py).
- Không thêm dependency Ollama SDK; adapter dùng HTTP API chuẩn bằng Python stdlib.
- Không tạo migration/DB table và chưa thay đổi Authorization/Calendar/LangGraph state.
- Verification được thực hiện **local**, không dùng GitHub Actions làm test gate.
