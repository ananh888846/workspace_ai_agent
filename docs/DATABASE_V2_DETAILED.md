# Workspace AI Agent — DATABASE V2 DETAILED

> Thiết kế database chi tiết chính thức cho Architecture V2.
>
> Trạng thái: **Schema source of truth — Database V2.1 CLOSED.** Migration 001 → 045 và hậu review 046 → 050 đã được verify trên PostgreSQL 18.6. Application runtime chưa triển khai.
>
> Tài liệu này triển khai chi tiết docs/DATABASE.md và phải nhất quán với ARCHITECTURE.md, AUTHORIZATION.md và DECISIONS.md.

---

# 1. Mục tiêu

Database V2 phải đáp ứng:

- Một User có thể có nhiều external account.
- Account metadata và Credential tách biệt.
- Identity, Authorization, Account, Resource và Data Package độc lập.
- Authorization kiểm tra capability, account, resource và package khi áp dụng.
- Credential chỉ được truy xuất sau Authorization = ALLOW.
- Device có identity riêng và không phải User.
- Observation, Event, Activity Session và Activity là các domain riêng.
- Conversation, Memory và Knowledge là các domain riêng.
- SQL giữ metadata, quan hệ, ownership, authorization, transaction và audit.
- Qdrant giữ vector retrieval; SQL giữ mapping và authorization metadata.
- Agent, Tool và Run phải có trace.
- Có thể thêm Google, Meta/Facebook, Zalo, Telegram, Home Assistant mà không phá Core.
- Không tạo trước domain tables nếu capability tương ứng chưa được duyệt.
- Organization là tenant boundary cho các domain scoped.
- Resource có parent/child hierarchy.
- Device có organization/resource binding nhưng độc lập với User.
- V2.1 bổ sung Activity Session, Task/Work Order, Agent-to-Agent communication và Anomaly.

---

# 2. Database engine và convention

## 2.1 Database engine

Thiết kế chuẩn:

- PostgreSQL
- JSONB cho metadata/config mở rộng.
- TIMESTAMPTZ cho timestamp.
- UUID/UUIDv7 cho primary key của core entities.

Không thiết kế schema phụ thuộc SQLite.

## 2.2 ID

Core entity dùng UUID/UUIDv7 theo một convention thống nhất.

Khuyến nghị UUIDv7 để có tính chất gần sequential theo thời gian, hỗ trợ index và truy vấn theo thời gian.

Mapping tables thuần quan hệ có thể dùng composite primary key khi phù hợp.

## 2.3 Timestamp

Tất cả timestamp dùng TIMESTAMPTZ và lưu UTC.

Client chuyển sang timezone của User khi hiển thị.

## 2.4 Soft delete

Không mặc định thêm deleted_at vào mọi bảng.

Chỉ dùng soft delete khi cần giữ lịch sử, khôi phục hoặc bảo toàn audit.

Authorization/credential không dùng soft delete để thay thế revoke/disable.

## 2.5 Status

Status là business state và phải là column rõ ràng.

Ví dụ:

- active
- disabled
- revoked
- expired

Giá trị cuối cùng được khóa trong application/domain contract trước migration.

## 2.6 JSONB

Chỉ dùng JSONB cho provider-specific metadata, configuration mở rộng, raw observation data và automation conditions/actions.

Không dùng JSONB thay cho user_id, account_id, resource_id, permission, role_id, package_id, request_id, status hoặc FK quan trọng.

---

# 3. Foreign Key và Delete policy

Core relationship phải có FK.

Ví dụ:

- user_accounts.user_id → users.id
- account_credentials.user_account_id → user_accounts.id
- account_grants.user_account_id → user_accounts.id
- resources.owner_user_id → users.id

Mặc định dùng ON DELETE RESTRICT đối với entity có ý nghĩa lịch sử hoặc authorization.

Có thể dùng ON DELETE CASCADE cho mapping thuần túy như:

- user_roles
- device_users
- agent_capabilities
- tool_capabilities
- data_package_resources

Không cascade tùy tiện trên business history hoặc audit.

### 3.1 V2.1 composite tenant FK contract

Các composite FK dưới đây là database-level requirement, không phải application-only rule:

- `account_grants(organization_id, owner_user_id) → organization_members(organization_id, user_id)`.
- `account_grants(organization_id, grantee_user_id) → organization_members(organization_id, user_id)`.
- `account_grants(user_account_id, owner_user_id) → user_accounts(id, user_id)`.
- `resources(parent_resource_id, organization_id) → resources(id, organization_id)` khi parent không NULL.
- `data_packages(organization_id, owner_user_id) → organization_members(organization_id, user_id)`.
- `data_package_versions(data_package_id, organization_id) → data_packages(id, organization_id)`.
- `data_package_resources(package_version_id, organization_id) → data_package_versions(id, organization_id)`.
- `data_package_resources(resource_id, organization_id) → resources(id, organization_id)`.
- `data_package_grants(package_version_id, organization_id) → data_package_versions(id, organization_id)`.
- `data_package_grants(organization_id, user_id) → organization_members(organization_id, user_id)`.
- `devices(resource_id, organization_id) → resources(id, organization_id)` khi resource không NULL.
- `resources(user_account_id, owner_user_id) → user_accounts(id, user_id)` khi account-backed.
- `user_sessions(organization_id, user_id) → organization_members(organization_id, user_id)`.
- `user_sessions(device_id, organization_id) → devices(id, organization_id)` khi device không NULL.
- `device_users(device_id, organization_id) → devices(id, organization_id)`.
- `device_users(organization_id, user_id) → organization_members(organization_id, user_id)`.
- `resource_permissions(resource_id, organization_id) → resources(id, organization_id)`.
- `resource_permissions(organization_id, user_id) → organization_members(organization_id, user_id)`.
- Tenant-scoped Activity/Task/A2A relations phải dùng cùng pattern `(id, organization_id)` hoặc equivalent database constraint để ngăn cross-organization reference.

Các bảng được target bởi composite FK phải có UNIQUE key tương ứng, ví dụ `UNIQUE(id, organization_id)`.


---

# 4. DOMAIN 00 — Organization / Tenant

## 4.1 organizations

Tenant/workspace boundary cho Family, Homestay, Smart Home và domain tương lai.

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| name | VARCHAR(255) | NO | — | |
| organization_type | VARCHAR(64) | NO | — | INDEX |
| status | VARCHAR(32) | NO | active | INDEX |
| metadata | JSONB | NO | {} | |
| created_at | TIMESTAMPTZ | NO | now() | INDEX |
| updated_at | TIMESTAMPTZ | NO | now() | |

## 4.3 Organization scope rule

Các domain có ownership/lifecycle trực tiếp theo tenant phải mang `organization_id` để database và runtime cùng enforce tenant isolation. V2.1 khóa tenant scope rõ cho:

- `resources`
- `devices`
- `account_grants`
- `data_packages`
- `data_package_versions`
- `data_package_resources`
- `data_package_grants`
- `events`
- `activity_sessions`
- `activities`
- `tasks`
- `agent_messages`
- `agent_tasks`
- `agent_permissions`
- `anomalies`
- `anomaly_evidence`

Organization membership không thay thế capability/account/resource/package authorization. Với quan hệ parent/child hoặc entity tham chiếu entity tenant-scoped, phải enforce cùng organization bằng composite FK hoặc constraint tương đương; không chỉ kiểm tra ở application.

## 4.2 organization_members

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| organization_id | UUID | NO | — | PK, FK |
| user_id | UUID | NO | — | PK, FK |
| member_role | VARCHAR(64) | NO | member | INDEX |
| status | VARCHAR(32) | NO | active | INDEX |
| joined_at | TIMESTAMPTZ | NO | now() | |
| created_at | TIMESTAMPTZ | NO | now() | |

Primary key: (organization_id, user_id). Membership không thay thế capability/resource authorization.

---

# 5. DOMAIN 01 — Identity

## 5.1 users

Mục đích: identity trung tâm.

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| name | VARCHAR(200) | NO | — | |
| email | VARCHAR(320) | YES | NULL | UNIQUE |
| phone | VARCHAR(32) | YES | NULL | |
| status | VARCHAR(32) | NO | active | INDEX |
| created_at | TIMESTAMPTZ | NO | now() | INDEX |
| updated_at | TIMESTAMPTZ | NO | now() | |

Rules:

- Email unique khi có giá trị.
- Nếu cần case-insensitive email, chuẩn hóa theo PostgreSQL policy.
- status không thay thế authorization.

Relationships:

- users 1:N user_sessions
- users 1:N user_accounts
- users N:N roles
- users 1:N resources
- users 1:N data_packages

## 5.2 user_sessions

Mục đích: authenticated session.

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| user_id | UUID | NO | — | FK, INDEX |
| session_token_hash | VARCHAR(255) | NO | — | UNIQUE |
| device_id | UUID | YES | NULL | FK, INDEX |
| ip_address | INET | YES | NULL | |
| user_agent | TEXT | YES | NULL | |
| started_at | TIMESTAMPTZ | NO | now() | |
| expires_at | TIMESTAMPTZ | NO | — | INDEX |
| last_activity_at | TIMESTAMPTZ | YES | NULL | INDEX |
| revoked_at | TIMESTAMPTZ | YES | NULL | |
| created_at | TIMESTAMPTZ | NO | now() | |

Không lưu session token plaintext.

---

 # 6. DOMAIN 02 — External Accounts

## 5.1 user_accounts

Đại diện một external account mà User sở hữu hoặc kết nối.

Ví dụ một User có nhiều Google account, Facebook account, Zalo account hoặc Telegram account.

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| user_id | UUID | NO | — | FK, INDEX |
| provider | VARCHAR(64) | NO | — | INDEX |
| account_type | VARCHAR(64) | NO | — | |
| external_account_id | VARCHAR(255) | NO | — | INDEX |
| display_name | VARCHAR(255) | YES | NULL | |
| email | VARCHAR(320) | YES | NULL | |
| status | VARCHAR(32) | NO | active | INDEX |
| metadata | JSONB | NO | {} | |
| created_at | TIMESTAMPTZ | NO | now() | INDEX |
| updated_at | TIMESTAMPTZ | NO | now() | |

Base unique:

UNIQUE(provider, external_account_id)

Constraint bổ sung phục vụ ownership integrity:

UNIQUE(id, user_id)

Nếu provider có namespace riêng, constraint được mở rộng trong provider contract.

Relationships:

- users 1:N user_accounts
- user_accounts 1:N account_credentials
- user_accounts 1:N account_grants
- user_accounts 1:N resources

## 5.2 account_credentials

Mục đích: lưu credential bảo mật của external account.

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| user_account_id | UUID | NO | — | FK, INDEX |
| credential_type | VARCHAR(64) | NO | — | |
| encrypted_value | BYTEA/TEXT | NO | — | |
| expires_at | TIMESTAMPTZ | YES | NULL | INDEX |
| scopes | JSONB | NO | [] | |
| status | VARCHAR(32) | NO | active | INDEX |
| created_at | TIMESTAMPTZ | NO | now() | |
| updated_at | TIMESTAMPTZ | NO | now() | |

Security:

- Không plaintext.
- Không log.
- Không đưa vào AgentContext.
- Không đưa vào prompt.
- Không đưa vào audit log.
- Chỉ credential resolver/service được phép truy cập.
- Chỉ truy cập sau Authorization ALLOW.

---

 # 7. DOMAIN 03 — Authorization

## 6.1 roles

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| name | VARCHAR(100) | NO | — | UNIQUE |
| description | TEXT | YES | NULL | |
| created_at | TIMESTAMPTZ | NO | now() | |
| updated_at | TIMESTAMPTZ | NO | now() | |

## 6.2 permissions

Permission mô tả resource/action.

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| resource | VARCHAR(100) | NO | — | |
| action | VARCHAR(100) | NO | — | |
| description | TEXT | YES | NULL | |
| created_at | TIMESTAMPTZ | NO | now() | |

Unique:

UNIQUE(resource, action)

Ví dụ:

- calendar.read
- calendar.write
- drive.read
- drive.write
- home.control

## 6.3 user_roles

| Column | Type | Null | Key |
|---|---|---:|---|
| user_id | UUID | NO | PK, FK |
| role_id | UUID | NO | PK, FK |
| created_at | TIMESTAMPTZ | NO | |

Primary key:

(user_id, role_id)


## 6.4 role_permissions

Mapping chính thức giữa Role và Permission. Role không tự động có mọi permission.

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| role_id | UUID | NO | — | PK, FK |
| permission_id | UUID | NO | — | PK, FK |
| created_at | TIMESTAMPTZ | NO | now() | |

Primary key:

(role_id, permission_id)

Role chỉ có capability permission được map rõ ràng tại bảng này.

## 6.5 account_grants

Cho phép một User sử dụng external account của User khác.

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| organization_id | UUID | NO | — | FK, INDEX |
| owner_user_id | UUID | NO | — | FK, INDEX |
| grantee_user_id | UUID | NO | — | FK, INDEX |
| user_account_id | UUID | NO | — | FK, INDEX |
| scope | JSONB | NO | {} | |
| status | VARCHAR(32) | NO | active | INDEX |
| starts_at | TIMESTAMPTZ | YES | NULL | |
| expires_at | TIMESTAMPTZ | YES | NULL | INDEX |
| revoked_at | TIMESTAMPTZ | YES | NULL | |
| created_at | TIMESTAMPTZ | NO | now() | |

Unique:\n\nUNIQUE(id, organization_id)\n\nBusiness constraints:

- `(organization_id, owner_user_id)` và `(organization_id, grantee_user_id)` phải thuộc `organization_members` của cùng organization.
- `(user_account_id, owner_user_id)` phải được enforce bằng composite FK tới `user_accounts(id, user_id)`; không chỉ kiểm tra ở application.
- owner_user_id phải là owner thực tế của user_account_id.
- Account grant là tenant-scoped; một grant chỉ có hiệu lực trong `organization_id` ghi trên grant.
- grantee_user_id là User được cấp quyền.
- Với account-backed resource, resources.user_account_id phải trỏ đúng external account cung cấp resource.
- Resource local không có external account có thể để user_account_id = NULL nếu provider contract cho phép.
- Account grant không thay thế capability permission.
- scope chỉ mô tả phạm vi grant.

Account Access:

Capability Permission AND Account Grant = Account Access

---

 # 8. DOMAIN 04 — Resources

## 7.1 resources

Đại diện resource cụ thể của provider.

Ví dụ Google Drive file, Google Calendar, Home Assistant entity hoặc Facebook Page.

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| organization_id | UUID | NO | — | FK, INDEX |
| parent_resource_id | UUID | YES | NULL | FK, INDEX |
| resource_type | VARCHAR(100) | NO | — | INDEX |
| provider | VARCHAR(64) | NO | — | INDEX |
| external_id | VARCHAR(255) | NO | — | INDEX |
| user_account_id | UUID | YES | NULL | FK, INDEX |
| owner_user_id | UUID | NO | — | FK, INDEX |
| name | VARCHAR(500) | YES | NULL | |
| status | VARCHAR(32) | NO | active | INDEX |
| metadata | JSONB | NO | {} | |
| created_at | TIMESTAMPTZ | NO | now() | |
| updated_at | TIMESTAMPTZ | NO | now() | |

Unique:

UNIQUE(provider, user_account_id, resource_type, external_id)
UNIQUE(id, organization_id)

Nếu `user_account_id` khác NULL, provider của resource phải khớp provider của user_account.

## 7.2 resource_permissions

Quyền trên resource cụ thể.

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| resource_id | UUID | NO | — | FK, INDEX |
| user_id | UUID | NO | — | FK, INDEX |
| action | VARCHAR(100) | NO | — | |
| effect | VARCHAR(16) | NO | allow | |
| created_at | TIMESTAMPTZ | NO | now() | |
| expires_at | TIMESTAMPTZ | YES | NULL | INDEX |

Unique:

UNIQUE(resource_id, user_id, action)

Resource permission không tự tạo capability permission.

---

 # 9. DOMAIN 05 — Data Package

## 8.1 data_packages

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| organization_id | UUID | NO | — | FK, INDEX |
| owner_user_id | UUID | NO | — | FK, INDEX |
| name | VARCHAR(255) | NO | — | |
| description | TEXT | YES | NULL | |
| package_type | VARCHAR(64) | NO | — | INDEX |
| status | VARCHAR(32) | NO | active | INDEX |
| created_at | TIMESTAMPTZ | NO | now() | |
| updated_at | TIMESTAMPTZ | NO | now() | |

## 8.2 data_package_versions

Package phải versioned. Package và mọi package child đều thuộc cùng organization.

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| organization_id | UUID | NO | — | FK, INDEX |
| data_package_id | UUID | NO | — | FK, INDEX |
| version | INTEGER | NO | — | |
| status | VARCHAR(32) | NO | draft | INDEX |
| created_by | UUID | NO | — | FK |
| created_at | TIMESTAMPTZ | NO | now() | |

Unique:

UNIQUE(data_package_id, version)
UNIQUE(id, organization_id)

## 8.3 data_package_resources

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| organization_id | UUID | NO | — | FK, INDEX |
| package_version_id | UUID | NO | — | FK, INDEX |
| resource_id | UUID | NO | — | FK, INDEX |
| access_mode | VARCHAR(32) | NO | read | |

Unique:

UNIQUE(package_version_id, resource_id)
UNIQUE(id, organization_id)

## 8.4 data_package_grants

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| organization_id | UUID | NO | — | FK, INDEX |
| package_version_id | UUID | NO | — | FK, INDEX |
| user_id | UUID | NO | — | FK, INDEX |
| permission | VARCHAR(100) | NO | — | |
| starts_at | TIMESTAMPTZ | YES | NULL | |
| expires_at | TIMESTAMPTZ | YES | NULL | INDEX |
| created_at | TIMESTAMPTZ | NO | now() | |
| revoked_at | TIMESTAMPTZ | YES | NULL | |

Unique:

UNIQUE(package_version_id, user_id, permission)
UNIQUE(id, organization_id)

Package grant không bypass capability, account hoặc resource authorization.

Tenant integrity:

- `data_package_versions.organization_id` = package organization.
- `data_package_resources.organization_id` = version/resource organization.
- `data_package_grants.organization_id` = version organization và user phải là member của organization.
- Package không được chứa resource ngoài organization.

---

 # 10. DOMAIN 06 — Devices

## 9.1 devices

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| organization_id | UUID | NO | — | FK, INDEX |
| resource_id | UUID | YES | NULL | FK, INDEX |
| device_uuid | UUID | NO | — | UNIQUE |
| device_type | VARCHAR(64) | NO | — | INDEX |
| name | VARCHAR(255) | YES | NULL | |
| status | VARCHAR(32) | NO | active | INDEX |
| firmware_version | VARCHAR(100) | YES | NULL | |
| created_at | TIMESTAMPTZ | NO | now() | |
| updated_at | TIMESTAMPTZ | NO | now() | |
| last_seen_at | TIMESTAMPTZ | YES | NULL | INDEX |

Tenant integrity:

- `devices.organization_id` is NOT NULL.
- Nếu `resource_id` khác NULL, resource phải cùng organization.

Device credential nếu cần phải được thiết kế như security domain riêng.

## 9.2 device_users

| Column | Type | Null | Key |
|---|---|---:|---|
| device_id | UUID | NO | PK, FK |
| user_id | UUID | NO | PK, FK |
| relationship | VARCHAR(64) | NO | |
| status | VARCHAR(32) | NO | INDEX |
| created_at | TIMESTAMPTZ | NO | |

Primary key:

(device_id, user_id)

## 9.3 device_capabilities

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| device_id | UUID | NO | — | FK, INDEX |
| capability | VARCHAR(100) | NO | — | |
| enabled | BOOLEAN | NO | true | |
| config | JSONB | NO | {} | |

Unique:

UNIQUE(device_id, capability)

---

 # 11. DOMAIN 07 — Observation / Event / Activity

## 10.1 observations

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| organization_id | UUID | NO | — | FK, INDEX |
| device_id | UUID | NO | — | FK, INDEX |
| observation_type | VARCHAR(100) | NO | — | INDEX |
| raw_data | JSONB | NO | {} | |
| confidence | NUMERIC(5,4) | YES | NULL | |
| created_at | TIMESTAMPTZ | NO | now() | INDEX |

## 10.2 events

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| event_uuid | UUID | NO | — | UNIQUE |
| event_type | VARCHAR(100) | NO | — | INDEX |
| organization_id | UUID | NO | — | FK, INDEX |
| user_id | UUID | YES | NULL | FK, INDEX |
| device_id | UUID | YES | NULL | FK, INDEX |
| source_type | VARCHAR(64) | NO | — | |
| source_id | UUID | YES | NULL | |
| resource_id | UUID | YES | NULL | FK, INDEX |
| occurred_at | TIMESTAMPTZ | NO | — | INDEX |
| confidence | NUMERIC(5,4) | YES | NULL | |
| status | VARCHAR(32) | NO | detected | INDEX |
| metadata | JSONB | NO | {} | |
| created_at | TIMESTAMPTZ | NO | now() | |

## 10.3 activity_sessions

Activity Session là lifecycle của một phiên hoạt động, gom các Event/Activity liên quan theo tenant/resource/user.

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| organization_id | UUID | NO | — | FK, INDEX |
| user_id | UUID | YES | NULL | FK, INDEX |
| resource_id | UUID | YES | NULL | FK, INDEX |
| session_type | VARCHAR(100) | NO | — | INDEX |
| started_at | TIMESTAMPTZ | NO | — | INDEX |
| ended_at | TIMESTAMPTZ | YES | NULL | |
| duration_seconds | INTEGER | YES | NULL | |
| status | VARCHAR(32) | NO | active | INDEX |
| confidence | NUMERIC(5,4) | YES | NULL | |
| source_event_id | UUID | YES | NULL | FK, INDEX |
| metadata | JSONB | NO | {} | |
| created_at | TIMESTAMPTZ | NO | now() | INDEX |
| updated_at | TIMESTAMPTZ | NO | now() | |

## 10.4 activities

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| organization_id | UUID | NO | — | FK, INDEX |
| user_id | UUID | YES | NULL | FK, INDEX |
| activity_type | VARCHAR(100) | NO | — | INDEX |
| resource_id | UUID | YES | NULL | FK, INDEX |
| started_at | TIMESTAMPTZ | NO | — | INDEX |
| ended_at | TIMESTAMPTZ | YES | NULL | |
| status | VARCHAR(32) | NO | active | INDEX |
| confidence | NUMERIC(5,4) | YES | NULL | |
| source_event_id | UUID | YES | NULL | FK, INDEX |
| activity_session_id | UUID | YES | NULL | FK, INDEX |
| metadata | JSONB | NO | {} | |
| created_at | TIMESTAMPTZ | NO | now() | INDEX |

Flow:

Observation → Event → Activity Session → Activity

AI inference không mặc định là fact.

---

 # 12. DOMAIN 08 — Conversation

## 11.1 conversations

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| user_id | UUID | NO | — | FK, INDEX |
| session_id | UUID | YES | NULL | FK, INDEX |
| title | VARCHAR(500) | YES | NULL | |
| status | VARCHAR(32) | NO | active | INDEX |
| created_at | TIMESTAMPTZ | NO | now() | INDEX |
| updated_at | TIMESTAMPTZ | NO | now() | |

## 11.2 messages

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| conversation_id | UUID | NO | — | FK, INDEX |
| role | VARCHAR(32) | NO | — | INDEX |
| content | TEXT | NO | — | |
| model | VARCHAR(100) | YES | NULL | |
| tokens | INTEGER | YES | NULL | |
| created_at | TIMESTAMPTZ | NO | now() | INDEX |

Message là conversation history, không tự động trở thành memory.

---

 # 13. DOMAIN 09 — Memory

## 12.1 memories

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| user_id | UUID | NO | — | FK, INDEX |
| memory_type | VARCHAR(64) | NO | — | INDEX |
| content | TEXT | NO | — | |
| importance | NUMERIC(5,4) | YES | NULL | |
| source_conversation_id | UUID | YES | NULL | FK, INDEX |
| status | VARCHAR(32) | NO | active | INDEX |
| created_at | TIMESTAMPTZ | NO | now() | |
| updated_at | TIMESTAMPTZ | NO | now() | |

Memory không thay thế Knowledge.

---

 # 14. DOMAIN 10 — Knowledge

## 13.1 knowledge_documents

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| resource_id | UUID | YES | NULL | FK, INDEX |
| title | VARCHAR(500) | YES | NULL | |
| source_type | VARCHAR(64) | NO | — | INDEX |
| source_id | VARCHAR(255) | YES | NULL | |
| version | VARCHAR(100) | NO | — | |
| checksum | VARCHAR(255) | NO | — | INDEX |
| status | VARCHAR(32) | NO | active | INDEX |
| created_at | TIMESTAMPTZ | NO | now() | |
| updated_at | TIMESTAMPTZ | NO | now() | |

Candidate unique:

UNIQUE(source_type, source_id, version, checksum)

Final constraint phải được kiểm tra theo provider.

## 13.2 knowledge_chunks

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| document_id | UUID | NO | — | FK, INDEX |
| chunk_index | INTEGER | NO | — | |
| content_hash | VARCHAR(255) | NO | — | INDEX |
| qdrant_point_id | VARCHAR(255) | NO | — | UNIQUE |
| token_count | INTEGER | YES | NULL | |
| created_at | TIMESTAMPTZ | NO | now() | |

Unique:

UNIQUE(document_id, chunk_index)

Qdrant giữ vector và payload cần thiết cho retrieval. SQL giữ document metadata, ownership, authorization, version, checksum và mapping.

Retrieval phải chạy trong authorization context.

---

 # 15. DOMAIN 11 — Agents / Tools / Runs

## 14.1 agents

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

## 14.2 agent_capabilities

| Column | Type | Null | Key |
|---|---|---:|---|
| agent_id | UUID | NO | PK, FK |
| capability | VARCHAR(100) | NO | PK |
| enabled | BOOLEAN | NO | |

Primary key:

(agent_id, capability)

Agent capability không thay thế User Authorization.

## 14.3 tools

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

## 14.4 tool_capabilities

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| tool_id | UUID | NO | — | PK, FK |
| capability | VARCHAR(100) | NO | — | PK |
| resource | VARCHAR(100) | YES | NULL | |
| action | VARCHAR(100) | YES | NULL | |
| requires_account | BOOLEAN | NO | false | |

Primary key:

(tool_id, capability)

## 14.5 agent_runs

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

## 14.6 tool_runs

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

Không lưu credential trong tool_runs.

## 14.7 agent_messages

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

## 14.8 agent_tasks

Agent Task là đơn vị công việc có lifecycle; không tự cấp permission.

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

## 14.9 agent_permissions

Permission này biểu diễn Agent nào được phép gọi/ủy quyền cho Agent nào trong một organization và scope cụ thể.

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

UNIQUE(grantor_agent_id, grantee_agent_id, capability, action, resource_id)

Agent Permission không thay thế User/Organization/Resource/Capability Authorization.

---

 # 16. DOMAIN 12 — Automation

## 15.1 automations

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| owner_user_id | UUID | NO | — | FK, INDEX |
| name | VARCHAR(255) | NO | — | |
| status | VARCHAR(32) | NO | active | INDEX |
| created_at | TIMESTAMPTZ | NO | now() | |
| updated_at | TIMESTAMPTZ | NO | now() | |

## 15.2 automation_triggers

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| automation_id | UUID | NO | — | FK, INDEX |
| event_type | VARCHAR(100) | NO | — | INDEX |
| conditions | JSONB | NO | {} | |

## 14.10 agent communication integrity

- sender/receiver agent phải tồn tại và thuộc cùng organization scope của permission/task/message.
- `agent_messages.agent_task_id` nếu có phải trỏ tới task cùng organization.
- `agent_tasks.target_resource_id` nếu có phải thuộc cùng organization.
- `agent_permissions.resource_id` nếu có phải thuộc cùng organization.
- Cross-organization agent delegation hiện không được phép trong V2.1.

## 14.11 anomalies

Anomaly là kết quả phát hiện sai lệch từ facts/events/activities/tasks; không phải kết luận fraud.

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| organization_id | UUID | NO | — | FK, INDEX |
| anomaly_type | VARCHAR(100) | NO | — | INDEX |
| severity | VARCHAR(32) | NO | medium | INDEX |
| status | VARCHAR(32) | NO | open | INDEX |
| detection_method | VARCHAR(100) | NO | — | |
| confidence | NUMERIC(5,4) | YES | NULL | |
| user_id | UUID | YES | NULL | FK, INDEX |
| device_id | UUID | YES | NULL | FK, INDEX |
| resource_id | UUID | YES | NULL | FK, INDEX |
| event_id | UUID | YES | NULL | FK, INDEX |
| activity_id | UUID | YES | NULL | FK, INDEX |
| task_id | UUID | YES | NULL | FK, INDEX |
| detected_at | TIMESTAMPTZ | NO | now() | INDEX |
| resolved_at | TIMESTAMPTZ | YES | NULL | |
| metadata | JSONB | NO | {} | |
| created_at | TIMESTAMPTZ | NO | now() | INDEX |
| updated_at | TIMESTAMPTZ | NO | now() | |

## 14.12 anomaly_evidence

Evidence phải truy ngược được về nguồn facts hợp lệ.

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| anomaly_id | UUID | NO | — | FK, INDEX |
| source_type | VARCHAR(64) | NO | — | INDEX |
| source_id | UUID | NO | — | INDEX |
| evidence_role | VARCHAR(64) | NO | supporting | |
| weight | NUMERIC(5,4) | YES | NULL | |
| metadata | JSONB | NO | {} | |
| created_at | TIMESTAMPTZ | NO | now() | INDEX |

Source type V2.1: `observation`, `event`, `activity_session`, `activity`, `task`, `device`, `resource`. Source phải cùng organization với anomaly.

## 15. DOMAIN 12 — Automation

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| automation_id | UUID | NO | — | FK, INDEX |
| action_type | VARCHAR(100) | NO | — | INDEX |
| config | JSONB | NO | {} | |

Automation action vẫn phải đi qua Authorization/Tool boundary khi thực thi.

---

 # 17. DOMAIN 13 — Audit

## 16.1 audit_logs

Trace security-sensitive operation.

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| request_id | UUID | NO | — | INDEX |
| organization_id | UUID | YES | NULL | FK, INDEX |
| user_id | UUID | YES | NULL | FK, INDEX |
| device_id | UUID | YES | NULL | FK, INDEX |
| capability | VARCHAR(100) | YES | NULL | INDEX |
| action | VARCHAR(100) | NO | — | INDEX |
| resource_type | VARCHAR(100) | YES | NULL | |
| resource_id | UUID | YES | NULL | INDEX |
| account_id | UUID | YES | NULL | FK, INDEX |
| package_version_id | UUID | YES | NULL | FK, INDEX |
| result | VARCHAR(32) | NO | — | INDEX |
| ip_address | INET | YES | NULL | |
| user_agent | TEXT | YES | NULL | |
| created_at | TIMESTAMPTZ | NO | now() | INDEX |
| metadata | JSONB | NO | {} | |

Không ghi access token, refresh token, API key, password, private key hoặc device secret.

---

 # 18. Authorization database model

Mô hình:

User
 ↓
Capability Permission
 ↓
Account Grant
 ↓
Resource Permission
 ↓
Data Package Grant nếu áp dụng
 ↓
ALLOW / DENY

Điều kiện:

Capability Permission
AND Account Access
AND Resource Access
AND Package Access nếu applicable
=
ALLOW

Thiếu hoặc DENY một điều kiện bắt buộc thì protected provider/tool không được gọi.

---

 # 19. Relationship map

Identity:

users
 ├── user_sessions
 ├── user_accounts
 │    └── account_credentials
 ├── user_roles ─── roles ─── permissions
 ├── account_grants ─── user_accounts
 ├── resources
 │    └── resource_permissions
 ├── data_packages
 │    └── data_package_versions
 │         ├── data_package_resources ─── resources
 │         └── data_package_grants
 ├── conversations
 │    └── messages
 ├── memories
 ├── automations
 │    ├── automation_triggers
 │    └── automation_actions
 └── agent_runs
      └── tool_runs

Device:

devices
 ├── device_users ─── users
 ├── device_capabilities
 └── observations
      ↓
    events
      ↓
 activity_sessions
      ↓
   activities

Task reconciliation:
tasks ─────► activity_sessions
tasks ─────► activities

Agent-to-Agent:
agents
 ├── agent_messages
 ├── agent_tasks
 └── agent_permissions

Anomaly:
anomalies ─────► anomaly_evidence
     ├──── events
     ├──── activities
     ├──── tasks
     ├──── devices
     └──── resources

Knowledge:

resources
 ↓
knowledge_documents
 ↓
knowledge_chunks
 ↓
Qdrant

---

 # 20. Index strategy

Identity:

- users(email)
- users(status)
- user_sessions(user_id)
- user_sessions(expires_at)
- user_sessions(last_activity_at)

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
- account_grants(organization_id)
- account_grants(owner_user_id)
- account_grants(grantee_user_id)
- account_grants(user_account_id)
- account_grants(status)
- account_grants(expires_at)
- resource_permissions(resource_id)
- resource_permissions(user_id)
- resource_permissions(expires_at)

Resource:

- resources(organization_id)
- resources(owner_user_id)
- resources(user_account_id)
- resources(provider)
- resources(resource_type)
- resources(external_id)
- resources(provider, user_account_id, resource_type, external_id)

Package:

- data_packages(organization_id)
- data_packages(owner_user_id)
- data_package_versions(organization_id)
- data_package_versions(data_package_id)
- data_package_resources(organization_id, package_version_id)
- data_package_resources(package_version_id)
- data_package_resources(resource_id)
- data_package_grants(organization_id, package_version_id)
- data_package_grants(package_version_id)
- data_package_grants(user_id)
- data_package_grants(expires_at)

Runtime:

- agent_runs(request_id)
- agent_runs(user_id)
- agent_runs(agent_id)
- tool_runs(agent_run_id)
- tool_runs(tool_id)
- tool_runs(account_id)
- audit_logs(request_id)
- audit_logs(user_id)
- audit_logs(resource_id)
- audit_logs(account_id)
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
- agent_messages(organization_id)
- agent_messages(receiver_agent_id, status)
- agent_tasks(organization_id)
- agent_tasks(assigned_agent_id, status)
- agent_tasks(request_id)
- agent_permissions(organization_id)
- agent_permissions(grantee_agent_id, capability, action)
- anomalies(organization_id)
- anomalies(status)
- anomalies(detected_at)
- anomaly_evidence(anomaly_id)
- audit_logs(request_id)
- audit_logs(user_id)
- audit_logs(resource_id)
- audit_logs(account_id)
- audit_logs(package_version_id)
- audit_logs(created_at)

Không tạo quá nhiều index trước khi có query thực tế.

---

 # 21. Integrity constraints

## Account ownership

`account_grants(user_account_id, owner_user_id)` phải có composite FK tới `user_accounts(id, user_id)` để database tự enforce owner đúng account.

## Resource ownership

resources.owner_user_id phải là User sở hữu resource theo provider synchronization policy.

`resources` phải có UNIQUE(id, organization_id) để hỗ trợ composite FK cho parent/resource references.

`devices` phải có UNIQUE(id, organization_id) để hỗ trợ composite FK khi bind device → resource.

Các resource/device/task/agent references có organization scope phải dùng composite FK `(referenced_id, organization_id)` ở những quan hệ cần database-enforced tenant isolation.

## Data Package tenant integrity

- `data_packages.organization_id` là bắt buộc.
- `data_package_versions.organization_id` phải trùng package.
- `data_package_resources.organization_id` phải trùng package version và resource.
- `data_package_grants.organization_id` phải trùng package version và user phải thuộc organization.
- Package không được chứa resource khác organization.

## Package version

Không cho phép duplicate:

(data_package_id, version)

## Package resource

Không cho duplicate:

(package_version_id, resource_id)

## Capability

Không cho duplicate:

(resource, action)

## Credential

Mọi credential phải thuộc một user_account.

## Resource account binding

Resource có provider/external account phải tham chiếu user_account tương ứng; resource không gắn external account chỉ được phép khi provider/domain contract định nghĩa rõ.

## Organization integrity

- `account_grants.organization_id` phải có owner và grantee là member của cùng organization.
- `resources.organization_id` và `devices.organization_id` là NOT NULL.
- `resources.parent_resource_id` phải tham chiếu resource cùng `organization_id`.
- `devices.resource_id` phải tham chiếu resource cùng `organization_id`.
- `data_package_versions` phải tham chiếu package cùng `organization_id`.
- `data_package_resources` phải tham chiếu package version và resource cùng `organization_id`.
- `data_package_grants` phải tham chiếu package version và member cùng `organization_id`.
- Các bảng V2.1 có `organization_id` phải reject foreign reference khác organization.
- `agent_permissions` không cho phép grantor/grantee khác organization.
- `anomaly_evidence` không được tham chiếu source khác organization.
- Cross-organization Agent-to-Agent delegation bị DENY trong V2.1.

## Activity / Task reconciliation

- Activity Session và Task phải cùng organization.
- Activity thuộc Activity Session phải cùng organization.
- Task resource/user phải hợp lệ trong organization.
- Activity không tự chứng minh Task hoàn thành nếu không có evidence.

---

 # 22. Migration order

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

Đây là logical rollout order. Tên migration thực tế sẽ theo framework được chọn sau khi source architecture được chốt.

---

 # 23. Transaction boundaries

Các operation quan trọng phải transactionally consistent.

Ví dụ Account:

BEGIN
  create user_account
  create encrypted credential metadata
COMMIT

Data Package:

BEGIN
  create package version
  add package resources
  create/update grants
COMMIT

Không commit một phần khiến package version không nhất quán.

Provider API call không nên nằm trong DB transaction dài nếu provider không hỗ trợ transaction.

---

 # 24. Credential access boundary

Đúng:

Request
 ↓
Authentication
 ↓
Authorization
 ↓
ALLOW
 ↓
Credential Resolver
 ↓
account_credentials
 ↓
Provider Tool

Sai:

Request
 ↓
account_credentials
 ↓
LLM
 ↓
Authorization

---

 # 25. Knowledge authorization

Đúng:

User
 ↓
Capability Permission
 ↓
Resource/Package Authorization
 ↓
SQL authorization filter
 ↓
Knowledge metadata
 ↓
Qdrant retrieval
 ↓
Authorized chunks only

Không được search toàn bộ Qdrant rồi mới kiểm tra permission.

Nếu Qdrant cần pre-filter, authorization metadata phù hợp phải được đưa vào payload/index.

SQL vẫn là source of truth cho ownership/access policy.

---

 # 26. Audit requirements

Protected operation nên có tối thiểu:

- request_id
- user_id
- device_id nếu có
- action
- resource
- account
- result
- timestamp

Operation phức tạp có thể tham chiếu:

- agent_run_id
- tool_run_id
- package_version_id

Không lưu secret.

---

 # 27. Performance strategy

Không denormalize toàn bộ schema trước khi có benchmark.

Ưu tiên:

1. FK đúng.
2. Unique đúng.
3. Index theo query thực tế.
4. Authorization query có index.
5. Pagination.
6. Transaction ngắn.
7. Qdrant cho vector retrieval.
8. Cache sau khi benchmark chứng minh cần.

Các bảng lớn trong tương lai như messages, observations, events, audit_logs và tool_runs có thể partition/archive theo thời gian khi dữ liệu thực tế yêu cầu.

---

 # 28. Backup / restore

Production database phải có:

- automated backup;
- point-in-time recovery nếu deployment hỗ trợ;
- encrypted backup;
- restore test định kỳ;
- credential encryption key backup strategy riêng;
- không lưu secret plaintext trong logs.

Backup database không thay thế key management.

---

 # 29. Database security boundary

Không commit vào Git:

- DATABASE_URL
- database password
- encryption key
- OAuth token
- refresh token
- API key

Application chỉ được cấp DB permission cần thiết.

Credential storage phải được giới hạn quyền truy cập ở database/service layer.

---

 # 30. Core Database vs Domain Extensions

Không tạo trước:

- medications
- prescriptions
- social_posts
- facebook_pages
- zalo_messages
- home_assistant_entities

nếu capability tương ứng chưa được duyệt.

Capability mới:

Capability
 ↓
Decision Log
 ↓
Domain design
 ↓
Database extension
 ↓
Migration
 ↓
Runtime verification

---

 # 31. ERD logical summary

                         users
                           │
       ┌───────────────────┼─────────────────────┐
       │                   │                     │
       ▼                   ▼                     ▼
 user_sessions       user_accounts             roles
                           │                ▲      │
                           ▼                │      ▼
                   account_credentials   user_roles permissions
                           │
                           ▼
                    account_grants
                           │
                           ▼
                       resources
                           │
                           ▼
                  resource_permissions

 users
   │
   ▼
data_packages
   │
   ▼
data_package_versions
   ├────────────► data_package_resources ─────► resources
   └────────────► data_package_grants

 devices
   ├────────────► device_users ───────────────► users
   ├────────────► device_capabilities
   └────────────► observations
                       │
                       ▼
                     events
                       │
                       ▼
                    activities

 users ─────► conversations ─────► messages
   │
   └────────► memories

 resources ─────► knowledge_documents ─────► knowledge_chunks ─────► Qdrant

 agents ─────► agent_capabilities
   │
   ├────────► agent_runs ─────► tool_runs ─────► tools
   ├────────► agent_messages
   ├────────► agent_tasks
   └────────► agent_permissions

 observations
      ↓
    events
      ↓
 activity_sessions
      ↓
   activities

tasks ─────► activity_sessions / activities

anomalies ─────► anomaly_evidence

 users ─────► automations
                 ├────► automation_triggers
                 └────► automation_actions

                         audit_logs

---

 # 32. Database V2 acceptance checklist

Schema chỉ ready for implementation khi:

- [ ] PostgreSQL được chọn.
- [ ] UUID/UUIDv7 convention được khóa.
- [ ] UTC timestamp convention được khóa.
- [ ] User/account model được khóa.
- [ ] Credential boundary được khóa.
- [ ] Role/permission model được khóa.
- [ ] Role-to-permission mapping được khóa.
- [ ] Organization tenant boundary và scope rules được khóa.
- [ ] Account grant model được khóa.
- [ ] Account grant organization scope được khóa.
- [ ] Resource authorization được khóa.
- [ ] Data Package versioning được khóa.
- [ ] Data Package organization scope được khóa.
- [ ] Device identity tách khỏi User.
- [ ] Observation/Event/Activity Session/Activity tách biệt.
- [ ] Task/Work Order và Activity reconciliation được xác định.
- [ ] Conversation/Memory/Knowledge tách biệt.
- [ ] Agent-to-Agent message/task/permission được xác định.
- [ ] Anomaly/Evidence model và organization isolation được xác định.
- [ ] Qdrant mapping được xác định.
- [ ] Agent/Tool/Run trace được xác định.
- [ ] Audit model được xác định.
- [ ] FK strategy được xác định.
- [ ] Unique constraints được xác định.
- [ ] Index strategy được xác định.
- [ ] Delete behavior được review.
- [ ] Migration order được review.
- [ ] Runtime authorization test cases được chuẩn bị.
- [ ] Composite tenant/resource integrity constraints được review.
- [ ] Agent-to-Agent cross-organization denial được review.
- [ ] Anomaly evidence source integrity được review.

---

 # 33. Runtime verification bắt buộc

Database implementation không hoàn thành chỉ vì migration chạy thành công.

## Test A — Owner

User A
 ↓
Google Account A
 ↓
Resource A
 ↓
ALLOW
 ↓
Provider call

## Test B — Granted account

User B
 ↓
Account Grant → Account A
 ↓
Resource Permission
 ↓
ALLOW
 ↓
Provider call

## Test C — Denied account

User C
 ↓
Account A
 ↓
DENY
 ↓
Provider call = NOT CALLED
Credential = NOT RESOLVED

## Test D — Package

User B
 ↓
Package Grant
 ↓
Package Version
 ↓
Authorized Resource
 ↓
ALLOW

## Test E — Unauthorized Knowledge

User C
 ↓
Knowledge search
 ↓
No Resource/Package authorization
 ↓
Unauthorized chunks = 0

Runtime gate phải kiểm tra side effect/provider call thực tế, không chỉ HTTP response.

## Test F — Role permission

User → Role → role_permissions → Capability Permission

Role không có permission tương ứng phải bị DENY.

---

 # 34. Chốt trạng thái

DATABASE_V2_DETAILED.md là schema design blueprint V2.1, chưa phải implementation.

Schema V2 đã được review nội bộ theo các dependency và authorization invariants; các điểm bắt buộc gồm role-to-permission mapping, resource-to-account binding và migration FK order.

Schema V2.1 chốt thêm: `role_permissions`, composite ownership FK cho `account_grants`, account-grant organization scope, data-package organization scope, resource/provider-account consistency, `resources.organization_id`/`devices.organization_id` bắt buộc và migration numbering không trùng. Migration order được kiểm tra theo dependency FK, đặc biệt `users` phải được tạo trước `organization_members`.

Trình tự tiếp theo:

DATABASE_V2_DETAILED.md
 ↓
Review schema
 ↓
Review ERD
 ↓
Review authorization constraints
 ↓
Chốt migration contract
 ↓
Thiết kế source tree
 ↓
Implement Phase 1
 ↓
Runtime Verification

Không tạo migration trước khi Database V2 được chốt.


---

# V2.1 Migration Review Lock — 2026-09-21 09:35 +07:00

- Agent là tenant-scoped: thêm organization_id bắt buộc; UNIQUE(organization_id, name); các quan hệ Agent Task/Permission/Message dùng composite tenant FK.
- Task/Work Order đã khóa schema: id, organization_id, parent_task_id, created_by_user_id, assigned_user_id, title, description, task_type, priority, status, resource_id, source_event_id, due_at, started_at, completed_at, metadata, created_at, updated_at.
- Observations thêm organization_id bắt buộc để hỗ trợ tenant FK cho Evidence.
- Anomaly Evidence bỏ polymorphic source_type/source_id; dùng bảy nullable source FK: observation_id, event_id, activity_session_id, activity_id, task_id, device_id, resource_id; CHECK đúng một source; mọi source FK phải cùng organization.
- Automations, automation_triggers và automation_actions đều tenant-scoped bằng organization_id và composite FK.
- Các quy tắc trên là quyết định chốt và thay thế các implementation gate cũ.


---

# V2.1 Verification Update — 2026-09-21 08:30:00 +07:00

- PostgreSQL thực tế: **18.6**.
- Database test được xác nhận sạch trước Migration 001 → 010.
- Migration 001 → 010: **PASS**.
- Acceptance AT-001 → AT-008: **PASS**.
- Acceptance transaction kết thúc bằng **ROLLBACK**.
- Schema contract 001 → 010 đã được verify thực tế; các domain 011 → 045 vẫn theo migration gate riêng.

---

# V2.1 Migration 011 → 020 Review Correction — 2026-09-21 10:00:00 +07:00

Before production SQL, the schema source of truth was hardened so session/device/user relationships cannot cross organization boundaries. Resource account ownership is also enforced with a composite ownership FK; provider/account compatibility remains a database-level invariant.


## Migration 011 → 020 Additional Tenant Lock — 2026-09-21 10:05:00 +07:00

resource_permissions is tenant-scoped and cannot grant a resource to a user from another organization.

## Verification Gate — Migration 011 → 020

Migration 011 → 020 đã được chạy và kiểm thử thực tế trên PostgreSQL 18.6.

- AT-011 → AT-022: **12/12 PASS**
- Resource hierarchy và resource permission tenant isolation: **PASS**
- Resource/account ownership và provider compatibility: **PASS**
- Data Package tenant integrity: **PASS**
- Device/resource và user session tenant integrity: **PASS**
- Device capability uniqueness: **PASS**
- Acceptance transaction kết thúc bằng ROLLBACK.
- Database gate 011 → 020: **CLOSED**.


# Migration 021 → 030 Schema Lock — 2026-09-21

- `observations.organization_id` là bắt buộc; observation/device phải cùng organization bằng composite FK.
- Event, Activity Session và Activity có tenant composite FK cho device/resource/event/session references.
- Task/Work Order schema chính thức: `id`, `organization_id`, `parent_task_id`, `created_by_user_id`, `assigned_user_id`, `title`, `description`, `task_type`, `priority`, `status`, `resource_id`, `source_event_id`, `due_at`, `started_at`, `completed_at`, `metadata`, `created_at`, `updated_at`.
- Conversation và Memory vẫn user-owned theo contract hiện hành.
- Knowledge Document/Chunk dùng SQL metadata/authorization làm source of truth; Qdrant chỉ là retrieval store.
- Chưa tạo production SQL cho 021 → 030.
# V2.1 Migration 031 → 033 Schema Lock — 2026-09-21 17:35 +07:00

- `agents` là tenant-scoped: thêm `organization_id UUID NOT NULL`, FK tới `organizations(id)`, và UNIQUE(`organization_id`, `name`).
- `agent_capabilities` kế thừa tenant scope từ `agents`; PK vẫn là (`agent_id`, `capability`) và agent_id phải tham chiếu agent hợp lệ.
- `tools` là shared/global catalog trong V2.1, không mang `organization_id`; identity `name` là UNIQUE toàn hệ thống.
- `tools` không cấp authorization; `tool_capabilities` mới mô tả capability contract và `requires_account` chỉ mô tả dependency.
- Migration 031 → 033 chỉ tạo Agent identity, Agent capability mapping và Tool catalog; chưa tạo Agent Run/Tool Run/A2A.


# V2.1 Migration 011 → 033 Integration Verification — 2026-09-21

- PostgreSQL thực tế: **18.6**.
- Integration acceptance: [database/tests/acceptance_011_033.sql](../database/tests/acceptance_011_033.sql).
- AT-035 → AT-040: **6/6 PASS**.
- Cross-tenant device → resource: **REJECT đúng**.
- Cross-tenant task → event: **REJECT đúng**.
- Transaction test kết thúc bằng **ROLLBACK**.
- **Integration gate 011 → 033: CLOSED**.
\n\n# V2.1 Migration 034 → 045 Production SQL Review Lock — 2026-09-21\n\n- Agent/Tool runtime trace và A2A đều enforce tenant boundary ở DB bằng composite FK.\n- Automation root/trigger/action đều tenant-scoped.\n- Anomaly Evidence dùng explicit seven source FKs, exactly-one CHECK; không dùng polymorphic source.\n- Audit Logs append-only trong normal runtime; audit metadata được DB trigger kiểm tra secret-key boundary.\n- Production SQL 034 → 045 đã được tạo. Chưa đánh dấu verification gate CLOSED cho đến khi PostgreSQL acceptance PASS.\n

---

# Post-V2.1 Schema Amendments — DBR Closure

## Tool Run execution account

`tool_runs` carries `organization_id`, `user_id` and optional `account_grant_id`. The execution user comes from `agent_runs`. Account context is either directly owned by that user or delegated through an active account grant. Database trigger validation is mandatory.

## Audit Log account context

`audit_logs` has optional `account_grant_id`. When `account_id` is present, `organization_id` and `user_id` are required and the account must be directly owned or validly delegated to that user at audit creation time.

## Resource identity

Resource uniqueness is split by account-backed versus local resources:

- Account-backed: `(provider,user_account_id,resource_type,external_id)`.
- Local: `(organization_id,provider,resource_type,external_id)` where `user_account_id IS NULL`.

This replaces the old single nullable-account UNIQUE constraint because PostgreSQL UNIQUE permits multiple NULL values and therefore cannot fully define local-resource identity.
