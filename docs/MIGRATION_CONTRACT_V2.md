# Workspace AI Agent — MIGRATION CONTRACT V2.1

> **Trạng thái:** LOCKED FOR MIGRATION DESIGN
>
> Mục đích: khóa contract database trước khi viết migration thực tế.
>
> PostgreSQL, schema V2.1, 45 migration units.
>
> DATABASE_V2_DETAILED.md vẫn là **schema source of truth** cho column/type/null/default/FK chi tiết.

## 1. Migration gate

~~~text
ARCHITECTURE V2.1
      ↓
DATABASE_V2_DETAILED.md
      ↓
MIGRATION_CONTRACT_V2.md
      ↓
ERD_V2.md
      ↓
FK / UNIQUE / CHECK
      ↓
INDEX
      ↓
Migration 001 → 045
      ↓
Seed / reference data
      ↓
Runtime Verification
~~~

Migration implementation không được tự ý thay đổi domain semantics.

Nếu phát hiện schema cần thay đổi: cập nhật DATABASE_V2_DETAILED.md; cập nhật ERD_V2.md nếu relationship đổi; cập nhật DECISIONS.md nếu là architectural decision; cập nhật CHANGELOG.md; sau đó mới sửa migration.

## 2. Database platform contract

- Engine: PostgreSQL.
- Không phụ thuộc SQLite.
- Core entity dùng UUID/UUIDv7.
- Timestamp dùng TIMESTAMPTZ, lưu UTC.
- JSONB chỉ dùng cho metadata/config/raw payload mở rộng.
- Không dùng JSONB thay thế user_id, organization_id, account_id, resource_id, permission, role_id, package_id, request_id, status hoặc FK quan trọng.

### Nullability/default

- PK: NOT NULL.
- FK bắt buộc theo schema: NOT NULL.
- FK optional: NULL.
- Business status: NOT NULL; default theo schema.
- metadata/config: NOT NULL DEFAULT '{}'.
- scopes: NOT NULL DEFAULT '[]'.
- created_at: NOT NULL DEFAULT now().
- updated_at: NOT NULL DEFAULT now() ở mutable tables.
- Không tự thêm deleted_at vào mọi bảng.

## 3. Foreign key và delete policy

Core relationship phải có FK.

Mặc định dùng ON DELETE RESTRICT cho:

- business history;
- authorization;
- credential;
- audit;
- run trace.

Có thể dùng ON DELETE CASCADE cho mapping thuần quan hệ đã được xác định:

- user_roles;
- role_permissions;
- device_users;
- agent_capabilities;
- tool_capabilities;
- data_package_resources.

Không cascade tùy tiện trên business history.

### Composite FK tenant integrity

Các entity tenant-scoped cần hỗ trợ cặp:

~~~text
(id, organization_id)
~~~

Database phải dùng composite FK cho các quan hệ cần enforce same-organization; không chỉ kiểm tra bằng application code.

Locked composite FK set:

~~~text
account_grants(organization_id, owner_user_id) → organization_members(organization_id, user_id)
account_grants(organization_id, grantee_user_id) → organization_members(organization_id, user_id)
account_grants(user_account_id, owner_user_id) → user_accounts(id, user_id)
resources(parent_resource_id, organization_id) → resources(id, organization_id)
resources(user_account_id, owner_user_id) → user_accounts(id, user_id)
data_packages(organization_id, owner_user_id) → organization_members(organization_id, user_id)
data_package_versions(data_package_id, organization_id) → data_packages(id, organization_id)
data_package_resources(package_version_id, organization_id) → data_package_versions(id, organization_id)
data_package_resources(resource_id, organization_id) → resources(id, organization_id)
data_package_grants(package_version_id, organization_id) → data_package_versions(id, organization_id)
data_package_grants(organization_id, user_id) → organization_members(organization_id, user_id)
devices(resource_id, organization_id) → resources(id, organization_id)
resource_permissions(resource_id, organization_id) → resources(id, organization_id)
resource_permissions(organization_id, user_id) → organization_members(organization_id, user_id)
user_sessions(organization_id, user_id) → organization_members(organization_id, user_id)
user_sessions(device_id, organization_id) → devices(id, organization_id)
device_users(device_id, organization_id) → devices(id, organization_id)
device_users(organization_id, user_id) → organization_members(organization_id, user_id)
~~~

Các target table phải có UNIQUE(id, organization_id) hoặc composite key tương đương.

## 4. Organization / tenant contract

organizations là tenant/business boundary.

User có thể thuộc nhiều organization. organization_members chỉ xác định tenant eligibility; không tự cấp application authorization.

Tenant-scoped V2.1:

- account_grants
- data_packages
- data_package_versions
- data_package_resources
- data_package_grants
- resources
- devices
- events
- activity_sessions
- activities
- tasks
- agent_messages
- agent_tasks
- agent_permissions
- anomalies
- anomaly_evidence

Locked invariants:

1. resource parent cùng organization;
2. device → resource cùng organization;
3. activity session → resource cùng organization;
4. activity → activity session cùng organization;
5. task → user/resource cùng organization;
6. agent task target resource cùng organization;
7. agent permission resource cùng organization;
8. grantor/grantee agent cùng organization;
9. anomaly evidence source cùng organization;
10. cross-organization Agent-to-Agent delegation = DENY.

## 5. Authorization integrity

### Role → Permission

Bắt buộc:

~~~text
roles
  ↓
role_permissions
  ↓
permissions
~~~

Unique:

~~~text
UNIQUE(permissions.resource, permissions.action)
PRIMARY KEY(role_permissions.role_id, role_permissions.permission_id)
~~~

Role không tự động có mọi permission.

### Account ownership

Bắt buộc:

~~~text
UNIQUE(user_accounts.id, user_accounts.user_id)

account_grants(user_account_id, owner_user_id)
    →
user_accounts(id, user_id)
~~~

Database phải tự enforce owner thực tế của account.

### Authorization formula

~~~text
Capability Permission
AND Account Access
AND Resource Access
AND Package Access (nếu applicable)
=
ALLOW
~~~

Thiếu hoặc DENY điều kiện bắt buộc thì protected provider/tool không được gọi.

## 6. Resource hierarchy

`resources.organization_id` và `devices.organization_id` là NOT NULL trong V2.1.

resources phải hỗ trợ organization scope và parent/child hierarchy.

Bắt buộc:

~~~text
UNIQUE(resources.id, resources.organization_id)
~~~

parent_resource_id phải tham chiếu resource cùng organization.

Nếu user_account_id khác NULL:

- account phải tồn tại;
- provider phải tương thích;
- owner_user_id phải phù hợp account ownership policy.

## 7. Data Package

Data Package là tenant-scoped trong V2.1. `organization_id` là NOT NULL trên package và các bảng package child để database có thể enforce same-organization integrity.

Lifecycle:

~~~text
data_packages
    ↓
data_package_versions
    ↓
data_package_resources
    +
data_package_grants
~~~

Unique:

~~~text
UNIQUE(data_package_id, version)
UNIQUE(package_version_id, resource_id)
UNIQUE(package_version_id, user_id, permission)
~~~

Package không chứa credential và không bypass capability/account/resource authorization.

Bắt buộc:

- package, version, package-resource và package-grant cùng `organization_id`;
- package-resource chỉ được chứa resource cùng organization;
- package-grant chỉ cấp cho user thuộc organization.

## 8. Device / Observation / Event

Device thuộc organization, có identity riêng và có thể bind resource.

Bắt buộc:

~~~text
UNIQUE(devices.device_uuid)
UNIQUE(devices.id, devices.organization_id)
~~~

Nếu resource_id có giá trị:

~~~text
devices(resource_id, organization_id)
    →
resources(id, organization_id)
~~~

Observation thuộc device.

Semantic flow:

~~~text
Observation → Event → Activity Session → Activity
~~~

AI inference không mặc định là fact.

## 9. Activity Session / Activity / Task

Activity Session là lifecycle của một phiên hoạt động, có organization, start/end, status và optional user/resource.

Activity nếu có activity_session_id phải cùng organization với session.

Task/Work Order là declared/assigned intent.

Activity là observed/recorded state.

Không coi Task hoàn thành chỉ vì Activity tồn tại; reconciliation cần evidence.

## 10. Conversation / Memory / Knowledge

Conversation/Message là history; Message không tự động trở thành Memory.

Memory là domain riêng, không thay Knowledge.

Knowledge:

- SQL giữ document metadata, ownership, authorization, version, checksum, chunk mapping.
- Qdrant giữ vector retrieval.
- Retrieval phải chạy trong authorization context.

Không retrieve toàn bộ Qdrant rồi mới lọc quyền.

## 11. Agent / Tool / Run

Agent có identity, type, status, config và capabilities.

Agent capability không thay User Authorization.

Tool có provider, version, status, config và capability contract.

requires_account chỉ mô tả dependency; không cấp quyền.

Agent Run phải trace request_id, organization_id, user_id, agent_id, optional conversation, timing và status.

Tool Run thuộc Agent Run và không lưu credential.

## 12. Agent-to-Agent

V2.1 chỉ cho delegation trong cùng organization.

Ba domain:

~~~text
agent_messages
agent_tasks
agent_permissions
~~~

Message/task không tự cấp permission.

Locked invariants:

- sender/receiver hợp lệ;
- task cùng organization;
- target resource cùng organization;
- permission cùng organization;
- grantor/grantee cùng organization;
- cross-organization delegation = DENY.

Unique:

~~~text
UNIQUE(
  grantor_agent_id,
  grantee_agent_id,
  capability,
  action,
  resource_id
)
~~~

## 13. Anomaly

Anomaly là evidence-based inference, không phải kết luận fraud.

Evidence source V2.1:

- observation;
- event;
- activity_session;
- activity;
- task;
- device;
- resource.

anomaly_evidence phải truy ngược được source hợp lệ.

Vì source_type/source_id là polymorphic reference, không giả định một FK trực tiếp tới tất cả source tables. Tenant integrity phải được enforce bằng transaction/constraint hoặc cơ chế database tương đương phù hợp implementation.

Evidence khác organization với anomaly = reject.

## 14. Automation

~~~text
automations
  ├── automation_triggers
  └── automation_actions
~~~

Automation không bypass Authorization/Tool boundary.

Provider call không được chạy chỉ vì automation row tồn tại.

## 15. Audit

audit_logs là security trace.

Protected operation tối thiểu trace:

- request_id;
- organization_id nếu có;
- user_id nếu có;
- device_id nếu có;
- capability;
- action;
- resource;
- account;
- package version nếu có;
- result;
- timestamp.

Không ghi access token, refresh token, API key, password, private key hoặc device secret.

## 16. Locked migration order

~~~text
001 organizations
002 users
003 organization_members

004 user_accounts
005 account_credentials

006 roles
007 permissions
008 user_roles
009 role_permissions
010 account_grants

011 resources
012 resource_permissions

013 data_packages
014 data_package_versions
015 data_package_resources
016 data_package_grants

017 devices
018 user_sessions
019 device_users
020 device_capabilities

021 observations
022 events
023 activity_sessions
024 activities
025 tasks

026 conversations
027 messages
028 memories

029 knowledge_documents
030 knowledge_chunks

031 agents
032 agent_capabilities
033 tools
034 tool_capabilities
035 agent_runs
036 tool_runs
037 agent_tasks
038 agent_permissions
039 agent_messages

040 automations
041 automation_triggers
042 automation_actions

043 anomalies
044 anomaly_evidence

045 audit_logs
~~~

Dependency rationale:

- resources trước devices vì devices.resource_id là FK;
- devices trước user_sessions vì user_sessions.device_id là FK;
- resources trước data_package_resources;
- agents/tools trước runs/A2A;
- agent_tasks trước agent_messages vì message có optional agent_task_id;
- anomalies trước anomaly_evidence;
- audit_logs cuối để trace được core entities.

Tên file migration thực tế phụ thuộc framework implementation.

## 17. Index contract

Index chính phải bao phủ FK lookup, authorization, tenant isolation và runtime trace.

Identity:
- users(email)
- users(status)
- user_sessions(user_id)
- user_sessions(expires_at)
- user_sessions(last_activity_at)

Organization:
- organization_members(user_id)
- organization_members(status)
- organization-scoped tables(organization_id)

Account:
- user_accounts(user_id)
- user_accounts(provider)
- user_accounts(external_account_id)
- user_accounts(provider, external_account_id)
- account_credentials(user_account_id)
- account_credentials(status)
- account_credentials(expires_at)

Authorization:
- user_roles(user_id)
- user_roles(role_id)
- account_grants(owner_user_id)
- account_grants(grantee_user_id)
- account_grants(user_account_id)
- account_grants(status)
- account_grants(expires_at)
- resource_permissions(resource_id)
- resource_permissions(user_id)
- resource_permissions(expires_at)

Resource:
- resources(owner_user_id)
- resources(user_account_id)
- resources(provider)
- resources(resource_type)
- resources(external_id)
- resources(parent_resource_id)
- resources(organization_id)

Package:
- data_packages(owner_user_id)
- data_package_versions(data_package_id)
- data_package_resources(package_version_id)
- data_package_resources(resource_id)
- data_package_grants(package_version_id)
- data_package_grants(user_id)
- data_package_grants(expires_at)

Runtime:
- agent_runs(request_id)
- agent_runs(organization_id)
- agent_runs(user_id)
- agent_runs(agent_id)
- tool_runs(agent_run_id)
- tool_runs(tool_id)
- tool_runs(account_id)

Activity/Task:
- activity_sessions(organization_id)
- activity_sessions(resource_id)
- activity_sessions(started_at)
- activities(organization_id)
- activities(activity_session_id)
- activities(resource_id)
- tasks(organization_id)
- tasks(assigned_user_id)
- tasks(resource_id)
- tasks(status)

A2A:
- agent_messages(organization_id)
- agent_messages(receiver_agent_id, status)
- agent_tasks(organization_id)
- agent_tasks(assigned_agent_id, status)
- agent_tasks(request_id)
- agent_permissions(organization_id)
- agent_permissions(grantee_agent_id, capability, action)

Anomaly:
- anomalies(organization_id)
- anomalies(status)
- anomalies(detected_at)
- anomaly_evidence(anomaly_id)

Audit:
- audit_logs(request_id)
- audit_logs(user_id)
- audit_logs(resource_id)
- audit_logs(account_id)
- audit_logs(package_version_id)
- audit_logs(created_at)

Không tạo index dư thừa chỉ vì FK tồn tại; composite index phải dựa trên query thực tế.

## 18. CHECK contract

Tối thiểu:

- confidence ∈ [0,1] khi không NULL;
- importance ∈ [0,1] khi không NULL;
- weight ∈ [0,1] khi không NULL;
- ended_at >= started_at khi cả hai tồn tại;
- completed_at >= started_at khi cả hai tồn tại;
- expires_at >= starts_at khi cả hai tồn tại;
- duration_seconds >= 0;
- token_count >= 0;
- chunk_index >= 0;
- version > 0;
- anomaly confidence ∈ [0,1] khi không NULL.

Không hard-code enum CHECK cho status nếu vocabulary cuối cùng chưa được application contract khóa.

## 19. Transaction contract

Atomic operations:

Account:
~~~text
BEGIN
  create account
  create credential metadata
COMMIT
~~~

Data Package:
~~~text
BEGIN
  create version
  attach resources
  create/update grants
COMMIT
~~~

Grant/revoke, A2A permission/task transition và anomaly + initial evidence phải nhất quán transactionally khi workflow yêu cầu.

Provider API call không nằm trong DB transaction dài.

## 20. Seed/reference data

Migration schema và seed data là hai khái niệm riêng.

Có thể seed:

- initial roles;
- initial permissions;
- capability definitions nếu domain contract yêu cầu.

Không seed:

- real users;
- real credentials;
- provider tokens;
- production resources;
- production device secrets.

Seed trở thành application contract phải được version hóa cùng release.

## 21. Rollback

Rollback theo dependency ngược:

~~~text
045 → 044 → ... → 001
~~~

Không drop parent trước child.

Destructive migration phải có explicit rollback policy; production rollback không mặc định DROP dữ liệu.

## 22. Migration acceptance tests

Schema:
- [ ] đủ 45 migration units;
- [ ] đủ PK;
- [ ] đủ FK;
- [ ] đủ composite tenant FK;
- [ ] đủ UNIQUE;
- [ ] đủ CHECK theo contract;
- [ ] đủ index chính;
- [ ] đúng UUID/TIMESTAMPTZ/JSONB convention.

Tenant isolation:
- [ ] account grant owner/grantee khác organization bị reject;
- [ ] package resource khác organization bị reject;
- [ ] package grant user khác organization bị reject;
- [ ] resource parent khác organization bị reject;
- [ ] device → resource khác organization bị reject;
- [ ] activity/session khác organization bị reject;
- [ ] task target khác organization bị reject;
- [ ] agent permission khác organization bị reject;
- [ ] A2A cross-organization bị reject;
- [ ] anomaly evidence khác organization bị reject.

Authorization:
- [ ] account grant owner mismatch bị reject;
- [ ] role không có permission không bypass;
- [ ] package grant không bypass resource/account authorization.

Security:
- [ ] credential không xuất hiện trong audit/tool-run/message contract;
- [ ] revoke/expiry biểu diễn được;
- [ ] audit trace có request_id.

Runtime boundary:
- [ ] Authorization DENY không resolve credential;
- [ ] Authorization DENY không execute protected tool;
- [ ] Authorization DENY không tạo provider side effect.

## 23. Explicit non-goals

V2.1 migration không tự thêm:

- medication;
- prescription;
- social post domain;
- advanced Home Assistant automation domain;
- provider-specific credential tables ngoài account_credentials;
- tenant scope cho Conversation/Memory/Knowledge/Data Package chỉ để đồng bộ hình thức;
- application logic vào migration;
- provider API calls trong migration.

Domain mới phải có architectural decision trước.

## 24. Source-of-truth policy

| Concern | Source |
|---|---|
| Architecture | ARCHITECTURE.md |
| Detailed columns/types/null/default/FK | DATABASE_V2_DETAILED.md |
| Migration dependency/order/acceptance | MIGRATION_CONTRACT_V2.md |
| Relationship view | ERD_V2.md |
| Authorization semantics | AUTHORIZATION.md |
| Architectural decisions | DECISIONS.md |
| Runtime acceptance | RUNTIME.md |
| Change history | CHANGELOG.md |

Nếu conflict:

1. Architecture/Decision quyết định semantics.
2. DATABASE_V2_DETAILED quyết định schema detail.
3. MIGRATION_CONTRACT quyết định migration implementation gate/order.
4. ERD phản ánh relationship.
5. Runtime test xác nhận behavior.

## 25. Final lock

Contract này khóa:

~~~text
[✓] PostgreSQL
[✓] UUIDv7 / TIMESTAMPTZ / JSONB convention
[✓] Nullability/default policy
[✓] FK/delete policy
[✓] Composite tenant integrity
[✓] UNIQUE/CHECK policy
[✓] Index policy
[✓] 45-step migration dependency order
[✓] Transaction boundary
[✓] Seed policy
[✓] Rollback policy
[✓] Runtime acceptance gate
[✓] No source-code implementation
~~~

Migration 001 → 010 đã được tạo, chạy trên PostgreSQL 18.6 sạch và acceptance test AT-001 → AT-008 đã PASS. Bước tiếp theo là triển khai theo gate Migration 011 → 020.


---

# Migration Review Lock — 2026-09-21 09:35 +07:00

Final lock: Agent tenant scope, Task schema, Anomaly Evidence explicit source FKs và Automation tenant scope đã được chốt. Không còn implementation gate nào trong bốn điểm này trước production SQL.


---

# Verification Update — 2026-09-21 08:30:00 +07:00

Migration 001 → 010 đã được verify thực tế trên PostgreSQL 18.6. Acceptance AT-001 → AT-008 đều PASS; test data được ROLLBACK. Contract gate 001 → 010 đã đóng.

---

# Migration 011 → 020 Pre-SQL Review Correction — 2026-09-21 10:00:00 +07:00

- user_sessions is tenant-scoped with organization_id and composite FKs to organization membership and device.
- device_users is tenant-scoped and cannot bind a device/user across organizations.
- resources account ownership is enforced by composite FK; provider/account compatibility must be enforced at database level, not application-only.


## Migration 011 → 020 Additional Tenant Lock — 2026-09-21 10:05:00 +07:00

resource_permissions is tenant-scoped. The resource and permission grantee must belong to the same organization at database level.
