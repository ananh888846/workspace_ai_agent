# Migration 031 → 040 — DDL Design V2.1

> Design only. Chưa phải SQL production và chưa chạy database thật.
>
> Source of truth: `DATABASE_V2_DETAILED.md`, `MIGRATION_CONTRACT_V2.md`, `ERD_V2.md`.
>
> Nhóm này thiết kế Agent Runtime, Tool Execution, Agent-to-Agent communication và Automation root entity.

## 1. Phạm vi

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

## 2. Migration 031 — agents

Agent là runtime definition. Theo schema source hiện tại, Agent chưa mang `organization_id`; tenant authorization được áp dụng tại các boundary sử dụng Agent.

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| name | VARCHAR(255) | NO | — | UNIQUE |
| agent_type | VARCHAR(64) | NO | — | INDEX |
| description | TEXT | YES | NULL | |
| status | VARCHAR(32) | NO | active | INDEX |
| config | JSONB | NO | {} | |
| created_at | TIMESTAMPTZ | NO | now() | |
| updated_at | TIMESTAMPTZ | NO | now() | |

Required:
- `name` UNIQUE.
- Agent configuration không chứa credential plaintext, access token, refresh token, private key hoặc secret.
- Agent capability không thay thế User/Organization/Resource Authorization.

Delete policy: RESTRICT khi Agent đã có runtime trace. Production implementation không được cascade làm mất `agent_runs`, `tool_runs`, A2A task/message history.

## 3. Migration 032 — agent_capabilities

Mapping capability thuần quan hệ.

| Column | Type | Null | Key |
|---|---|---:|---|
| agent_id | UUID | NO | PK, FK |
| capability | VARCHAR(100) | NO | PK |
| enabled | BOOLEAN | NO | |

Primary key:

`(agent_id, capability)`

Required:
- `agent_id → agents.id`.
- Duplicate capability trên cùng Agent → UNIQUE/PK REJECT.
- ON DELETE CASCADE được phép vì đây là mapping table.
- Capability chỉ mô tả khả năng kỹ thuật của Agent; không tự tạo authorization cho User.

Indexes:
- PK `(agent_id, capability)`.
- Nếu runtime cần lookup capability → `(capability, enabled)`.

## 4. Migration 033 — tools

Tool là runtime integration/execution definition.

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| name | VARCHAR(255) | NO | — | UNIQUE |
| provider | VARCHAR(64) | YES | NULL | INDEX |
| version | VARCHAR(64) | NO | — | |
| status | VARCHAR(32) | NO | active | INDEX |
| config | JSONB | NO | {} | |
| created_at | TIMESTAMPTZ | NO | now() | |
| updated_at | TIMESTAMPTZ | NO | now() | |

Required:
- `name` UNIQUE.
- Provider-specific configuration nằm trong `config`.
- Credential không được lưu trong `config`; credential phải qua Credential Resolver sau Authorization ALLOW.
- Tool status không thay thế authorization.

Delete policy: RESTRICT khi Tool đã có `tool_runs`.

## 5. Migration 034 — tool_capabilities

Mapping capability của Tool.

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| tool_id | UUID | NO | — | PK, FK |
| capability | VARCHAR(100) | NO | — | PK |
| resource | VARCHAR(100) | YES | NULL | |
| action | VARCHAR(100) | YES | NULL | |
| requires_account | BOOLEAN | NO | false | |

Primary key:

`(tool_id, capability)`

Required:
- `tool_id → tools.id`.
- ON DELETE CASCADE được phép.
- `resource/action` mô tả execution capability, không bypass Resource Permission.
- Nếu `requires_account=true`, runtime phải resolve account/grant/credential trước provider call.

## 6. Migration 035 — agent_runs

Trace một lần Agent xử lý request.

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| request_id | UUID | NO | — | INDEX |
| organization_id | UUID | NO | — | FK, INDEX |
| user_id | UUID | NO | — | FK, INDEX |
| agent_id | UUID | NO | — | FK, INDEX |
| conversation_id | UUID | YES | NULL | FK, INDEX |
| started_at | TIMESTAMPTZ | NO | now() | INDEX |
| finished_at | TIMESTAMPTZ | YES | NULL | |
| status | VARCHAR(32) | NO | running | INDEX |
| model | VARCHAR(100) | YES | NULL | |

Required:
- `organization_id → organizations.id`.
- `user_id → users.id`.
- `agent_id → agents.id`.
- `conversation_id → conversations.id` khi có.
- `finished_at >= started_at` khi finished_at khác NULL.
- Request trace phải giữ `request_id` để correlation.
- Không lưu credential hoặc provider secret trong run record.

Indexes:
- `(organization_id, started_at)`.
- `(organization_id, user_id, started_at)`.
- `(organization_id, status, started_at)`.
- `request_id`.

Delete policy: RESTRICT. Runtime trace không được mất do xóa User/Conversation/Agent.

## 7. Migration 036 — tool_runs

Trace một lần Tool được thực thi trong Agent Run.

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| agent_run_id | UUID | NO | — | FK, INDEX |
| tool_id | UUID | NO | — | FK, INDEX |
| account_id | UUID | YES | NULL | FK, INDEX |
| started_at | TIMESTAMPTZ | NO | now() | |
| finished_at | TIMESTAMPTZ | YES | NULL | |
| status | VARCHAR(32) | NO | running | INDEX |
| error | TEXT | YES | NULL | |

Required:
- `agent_run_id → agent_runs.id`.
- `tool_id → tools.id`.
- `account_id → user_accounts.id` khi có.
- `finished_at >= started_at` khi finished_at khác NULL.
- Không lưu access token, refresh token, API key hoặc credential plaintext.
- Error message phải được sanitize để không làm lộ secret.

Tenant/runtime rule:
- Tool Run kế thừa execution context từ Agent Run.
- Nếu account_id khác NULL, runtime phải chứng minh account/grant/resource authorization trước provider call.
- Không dùng `tool_runs` làm authorization source.

Indexes:
- `(agent_run_id, started_at)`.
- `(tool_id, started_at)`.
- `(account_id, started_at)` khi account_id khác NULL.

Delete policy: RESTRICT.

## 8. Migration 037 — agent_tasks

Agent Task là đơn vị công việc có lifecycle và hỗ trợ parent/child task.

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| organization_id | UUID | NO | — | FK, INDEX |
| parent_agent_task_id | UUID | YES | NULL | FK, INDEX |
| request_id | UUID | NO | — | INDEX |
| created_by_agent_id | UUID | NO | — | FK, INDEX |
| assigned_agent_id | UUID | NO | — | FK, INDEX |
| capability | VARCHAR(100) | NO | — | INDEX |
| action | VARCHAR(100) | NO | — | INDEX |
| target_resource_id | UUID | YES | NULL | FK, INDEX |
| status | VARCHAR(32) | NO | pending | INDEX |
| started_at | TIMESTAMPTZ | YES | NULL | |
| finished_at | TIMESTAMPTZ | YES | NULL | |
| result_metadata | JSONB | NO | {} | |
| created_at | TIMESTAMPTZ | NO | now() | INDEX |
| updated_at | TIMESTAMPTZ | NO | now() | |

Required:
- `organization_id → organizations.id`.
- `parent_agent_task_id → agent_tasks.id` khi có.
- `created_by_agent_id → agents.id`.
- `assigned_agent_id → agents.id`.
- `target_resource_id → resources.id` khi có.
- `finished_at >= started_at` khi cả hai khác NULL.
- Parent task và target resource phải cùng organization theo DB-level tenant constraint/equivalent contract.
- Cross-organization Agent delegation không được phép trong V2.1.

Indexes:
- `(organization_id, status, created_at)`.
- `(organization_id, assigned_agent_id, status)`.
- `(organization_id, capability, action, status)`.
- `parent_agent_task_id`.
- `target_resource_id`.

Delete policy: RESTRICT. Task history không cascade theo Agent/Resource.

## 9. Migration 038 — agent_permissions

Agent Permission mô tả quyền Agent A gọi/ủy quyền cho Agent B trong organization và resource scope.

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| organization_id | UUID | NO | — | FK, INDEX |
| grantor_agent_id | UUID | NO | — | FK, INDEX |
| grantee_agent_id | UUID | NO | — | FK, INDEX |
| capability | VARCHAR(100) | NO | — | INDEX |
| action | VARCHAR(100) | NO | — | INDEX |
| resource_id | UUID | YES | NULL | FK, INDEX |
| effect | VARCHAR(16) | NO | allow | |
| starts_at | TIMESTAMPTZ | YES | NULL | |
| expires_at | TIMESTAMPTZ | YES | NULL | INDEX |
| revoked_at | TIMESTAMPTZ | YES | NULL | |
| created_at | TIMESTAMPTZ | NO | now() | |

Unique:

`UNIQUE(grantor_agent_id, grantee_agent_id, capability, action, resource_id)`

Required:
- `organization_id → organizations.id`.
- `grantor_agent_id → agents.id`.
- `grantee_agent_id → agents.id`.
- `resource_id → resources.id` khi có.
- `expires_at >= starts_at` khi cả hai khác NULL.
- `effect` chỉ nhận contract value đã được application/domain contract khóa.
- Cross-organization delegation không được phép.

Important implementation gate:
- Schema hiện tại định nghĩa `agents` là global entity, không có `organization_id`.
- Vì vậy composite FK trực tiếp `(organization_id, agent_id)` chưa thể tạo với schema hiện tại.
- Trước production SQL, phải chọn một DB-level contract rõ ràng để chứng minh Agent được phép hoạt động trong organization (ví dụ organization-agent membership/binding), hoặc cập nhật source-of-truth schema.
- Không được giải quyết điểm này chỉ bằng application check nếu mục tiêu là tenant integrity database-level.

Delete policy: RESTRICT vì đây là authorization history.

## 10. Migration 039 — agent_messages

Message là transport/trace giữa các Agent; message không tự cấp permission.

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| organization_id | UUID | NO | — | FK, INDEX |
| sender_agent_id | UUID | NO | — | FK, INDEX |
| receiver_agent_id | UUID | NO | — | FK, INDEX |
| agent_task_id | UUID | YES | NULL | FK, INDEX |
| message_type | VARCHAR(64) | NO | — | INDEX |
| payload | JSONB | NO | {} | |
| status | VARCHAR(32) | NO | pending | INDEX |
| created_at | TIMESTAMPTZ | NO | now() | INDEX |
| processed_at | TIMESTAMPTZ | YES | NULL | |

Required:
- `organization_id → organizations.id`.
- `sender_agent_id → agents.id`.
- `receiver_agent_id → agents.id`.
- `agent_task_id → agent_tasks.id` khi có.
- sender/receiver phải thuộc cùng organization scope của message/task.
- `processed_at` không được sớm hơn `created_at` khi có.
- Payload không chứa credential/token/secret.

Important implementation gate:
- Giống Migration 038, Agent hiện là global entity nên DB-level same-organization binding chưa có target key.
- Trước production SQL phải khóa Agent ↔ Organization membership/binding hoặc một database-equivalent constraint.
- Không cho phép cross-organization A2A message.

Indexes:
- `(organization_id, created_at)`.
- `(organization_id, status, created_at)`.
- `(receiver_agent_id, status, created_at)`.
- `agent_task_id`.

Delete policy: RESTRICT. A2A trace phải được giữ.

## 11. Migration 040 — automations

Automation root entity hiện thuộc User; trigger/action là child migrations 041/042.

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| owner_user_id | UUID | NO | — | FK, INDEX |
| name | VARCHAR(255) | NO | — | |
| status | VARCHAR(32) | NO | active | INDEX |
| created_at | TIMESTAMPTZ | NO | now() | |
| updated_at | TIMESTAMPTZ | NO | now() | |

Required:
- `owner_user_id → users.id`.
- Automation status là lifecycle state, không phải authorization.
- Conditions/actions không nằm trực tiếp trong root table; dùng 041/042.
- Automation execution phải đi qua Authorization/Tool boundary.
- Không được lưu credential trực tiếp trong automation definition.

Indexes:
- `(owner_user_id, status, updated_at)`.
- Nếu runtime cần lịch sử theo thời gian, `(owner_user_id, created_at)`.

Delete policy: RESTRICT nếu automation đã được tham chiếu/executed; child cleanup chỉ theo policy của 041/042.

## 12. Dependency order

031 agents  
→ 032 agent_capabilities  
→ 033 tools  
→ 034 tool_capabilities  
→ 035 agent_runs  
→ 036 tool_runs  
→ 037 agent_tasks  
→ 038 agent_permissions  
→ 039 agent_messages  
→ 040 automations

Dependency notes:
- 032 cần 031.
- 034 cần 033.
- 035 cần organizations, users, agents, conversations.
- 036 cần agent_runs, tools, user_accounts.
- 037 cần organizations, agents, resources và chính agent_tasks cho parent.
- 038 cần organizations, agents, resources.
- 039 cần organizations, agents, agent_tasks.
- 040 cần users.
- 041/042 sẽ phụ thuộc 040.

## 13. Acceptance tests

AT-031 duplicate Agent name → UNIQUE REJECT.  
AT-032 deleting Agent with runtime history → RESTRICT.  
AT-033 duplicate Agent capability → PK/UNIQUE REJECT.  
AT-034 duplicate Tool capability → PK/UNIQUE REJECT.  
AT-035 Agent Run referencing nonexistent Agent/User/Organization → FK REJECT.  
AT-036 Tool Run referencing nonexistent Tool/Agent Run/Account → FK REJECT.  
AT-037 invalid Agent Task lifecycle time range → CHECK REJECT.  
AT-038 Agent Permission with invalid expiry range → CHECK REJECT.  
AT-039 A2A message with nonexistent task/Agent → FK REJECT.  
AT-040 Automation referencing nonexistent User → FK REJECT.

Tenant/A2A acceptance:
- Agent Task target resource from another organization → REJECT.
- Agent Permission resource from another organization → REJECT.
- Agent Message linked to task from another organization → REJECT.
- Cross-organization sender/receiver Agent delegation → REJECT.
- Runtime must not execute a Tool merely because Agent capability exists; User/Organization/Resource/Account authorization is still required.
- Tool Run must never expose credential material.
- Automation action must pass Authorization/Tool boundary before execution.

## 14. Implementation gate

- [x] Agent, Agent Capability, Tool và Tool Capability được tách thành runtime definitions/mappings.
- [x] Agent Run và Tool Run giữ execution trace.
- [x] Agent Task có lifecycle và tenant scope.
- [x] Agent Permission có explicit organization/resource scope.
- [x] Agent Message có tenant scope và task linkage.
- [x] Automation root được tách khỏi trigger/action children.
- [x] Credential không được lưu trong Agent/Tool/Run/A2A payload.
- [x] Tool execution không bypass User Authorization.
- [x] Cross-tenant Resource references được yêu cầu ở DB level.
- [ ] Agent ↔ Organization membership/binding phải được chốt trước production SQL để hoàn tất DB-level same-tenant enforcement cho 037–039.
- [ ] Exact Automation trigger/action contract sẽ được khóa ở Migration 041–042.
- [x] No production SQL, database, provider call or runtime code is introduced.

Kết luận: Migration 031 → 040 đã được thiết kế ở mức DDL contract. Trước SQL implementation, phải chốt DB-level Agent ↔ Organization binding cho A2A/Agent Task integrity; Migration 041–042 sẽ hoàn thiện Automation children.
