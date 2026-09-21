# Workspace AI Agent — DATABASE V2 DETAILED

> Thiết kế database chi tiết chính thức cho Architecture V2.
>
> Trạng thái: Design only. Chưa tạo migration, chưa tạo bảng thật, chưa viết application code.
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
- Observation, Event và Activity là các domain riêng.
- Conversation, Memory và Knowledge là các domain riêng.
- SQL giữ metadata, quan hệ, ownership, authorization, transaction và audit.
- Qdrant giữ vector retrieval; SQL giữ mapping và authorization metadata.
- Agent, Tool và Run phải có trace.
- Có thể thêm Google, Meta/Facebook, Zalo, Telegram, Home Assistant mà không phá Core.
- Không tạo trước domain tables nếu capability tương ứng chưa được duyệt.

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

---

# 4. DOMAIN 01 — Identity

## 4.1 users

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

## 4.2 user_sessions

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

# 5. DOMAIN 02 — External Accounts

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

# 6. DOMAIN 03 — Authorization

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

## 6.4 account_grants

Cho phép một User sử dụng external account của User khác.

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| owner_user_id | UUID | NO | — | FK, INDEX |
| grantee_user_id | UUID | NO | — | FK, INDEX |
| user_account_id | UUID | NO | — | FK, INDEX |
| scope | JSONB | NO | {} | |
| status | VARCHAR(32) | NO | active | INDEX |
| starts_at | TIMESTAMPTZ | YES | NULL | |
| expires_at | TIMESTAMPTZ | YES | NULL | INDEX |
| revoked_at | TIMESTAMPTZ | YES | NULL | |
| created_at | TIMESTAMPTZ | NO | now() | |

Business constraints:

- owner_user_id phải là owner thực tế của user_account_id.
- grantee_user_id là User được cấp quyền.
- Với account-backed resource, resources.user_account_id phải trỏ đúng external account cung cấp resource.
- Resource local không có external account có thể để user_account_id = NULL nếu provider contract cho phép.
- Account grant không thay thế capability permission.
- scope chỉ mô tả phạm vi grant.

Account Access:

Capability Permission AND Account Grant = Account Access

---

# 7. DOMAIN 04 — Resources

## 7.1 resources

Đại diện resource cụ thể của provider.

Ví dụ Google Drive file, Google Calendar, Home Assistant entity hoặc Facebook Page.

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
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

# 8. DOMAIN 05 — Data Package

## 8.1 data_packages

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| owner_user_id | UUID | NO | — | FK, INDEX |
| name | VARCHAR(255) | NO | — | |
| description | TEXT | YES | NULL | |
| package_type | VARCHAR(64) | NO | — | INDEX |
| status | VARCHAR(32) | NO | active | INDEX |
| created_at | TIMESTAMPTZ | NO | now() | |
| updated_at | TIMESTAMPTZ | NO | now() | |

## 8.2 data_package_versions

Package phải versioned.

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| data_package_id | UUID | NO | — | FK, INDEX |
| version | INTEGER | NO | — | |
| status | VARCHAR(32) | NO | draft | INDEX |
| created_by | UUID | NO | — | FK |
| created_at | TIMESTAMPTZ | NO | now() | |

Unique:

UNIQUE(data_package_id, version)

## 8.3 data_package_resources

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| package_version_id | UUID | NO | — | FK, INDEX |
| resource_id | UUID | NO | — | FK, INDEX |
| access_mode | VARCHAR(32) | NO | read | |

Unique:

UNIQUE(package_version_id, resource_id)

## 8.4 data_package_grants

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| package_version_id | UUID | NO | — | FK, INDEX |
| user_id | UUID | NO | — | FK, INDEX |
| permission | VARCHAR(100) | NO | — | |
| starts_at | TIMESTAMPTZ | YES | NULL | |
| expires_at | TIMESTAMPTZ | YES | NULL | INDEX |
| created_at | TIMESTAMPTZ | NO | now() | |
| revoked_at | TIMESTAMPTZ | YES | NULL | |

Unique:

UNIQUE(package_version_id, user_id, permission)

Package grant không bypass capability, account hoặc resource authorization.

---

# 9. DOMAIN 06 — Devices

## 9.1 devices

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| device_uuid | UUID | NO | — | UNIQUE |
| device_type | VARCHAR(64) | NO | — | INDEX |
| name | VARCHAR(255) | YES | NULL | |
| status | VARCHAR(32) | NO | active | INDEX |
| firmware_version | VARCHAR(100) | YES | NULL | |
| created_at | TIMESTAMPTZ | NO | now() | |
| updated_at | TIMESTAMPTZ | NO | now() | |
| last_seen_at | TIMESTAMPTZ | YES | NULL | INDEX |

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

# 10. DOMAIN 07 — Observation / Event / Activity

## 10.1 observations

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
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
| user_id | UUID | YES | NULL | FK, INDEX |
| device_id | UUID | YES | NULL | FK, INDEX |
| source_type | VARCHAR(64) | NO | — | |
| source_id | UUID | YES | NULL | |
| occurred_at | TIMESTAMPTZ | NO | — | INDEX |
| confidence | NUMERIC(5,4) | YES | NULL | |
| status | VARCHAR(32) | NO | detected | INDEX |
| metadata | JSONB | NO | {} | |
| created_at | TIMESTAMPTZ | NO | now() | |

## 10.3 activities

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| user_id | UUID | NO | — | FK, INDEX |
| activity_type | VARCHAR(100) | NO | — | INDEX |
| started_at | TIMESTAMPTZ | NO | — | INDEX |
| ended_at | TIMESTAMPTZ | YES | NULL | |
| status | VARCHAR(32) | NO | active | INDEX |
| confidence | NUMERIC(5,4) | YES | NULL | |
| source_event_id | UUID | YES | NULL | FK, INDEX |
| metadata | JSONB | NO | {} | |
| created_at | TIMESTAMPTZ | NO | now() | |

Flow:

Observation → Verification/Detection → Event → Activity

AI inference không mặc định là fact.

---

# 11. DOMAIN 08 — Conversation

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

# 12. DOMAIN 09 — Memory

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

# 13. DOMAIN 10 — Knowledge

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

# 14. DOMAIN 11 — Agents / Tools / Runs

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

---

# 15. DOMAIN 12 — Automation

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

## 15.3 automation_actions

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| automation_id | UUID | NO | — | FK, INDEX |
| action_type | VARCHAR(100) | NO | — | INDEX |
| config | JSONB | NO | {} | |

Automation action vẫn phải đi qua Authorization/Tool boundary khi thực thi.

---

# 16. DOMAIN 13 — Audit

## 16.1 audit_logs

Trace security-sensitive operation.

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| request_id | UUID | NO | — | INDEX |
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

# 17. Authorization database model

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

# 18. Relationship map

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
   activities

Knowledge:

resources
 ↓
knowledge_documents
 ↓
knowledge_chunks
 ↓
Qdrant

---

# 19. Index strategy

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
- resources(provider, user_account_id, resource_type, external_id)

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
- agent_runs(user_id)
- agent_runs(agent_id)
- tool_runs(agent_run_id)
- tool_runs(tool_id)
- tool_runs(account_id)
- audit_logs(request_id)
- audit_logs(user_id)
- audit_logs(resource_id)
- audit_logs(account_id)
- audit_logs(package_version_id)
- audit_logs(created_at)

Không tạo quá nhiều index trước khi có query thực tế.

---

# 20. Integrity constraints

## Account ownership

account_grants.owner_user_id phải khớp owner của user_account_id.

## Resource ownership

resources.owner_user_id phải là User sở hữu resource theo provider synchronization policy.

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

---

# 21. Migration order

001 users
002 devices
003 user_sessions

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

017 device_users
018 device_capabilities

018 observations
019 events
020 activities

021 conversations
022 messages
023 memories

024 knowledge_documents
025 knowledge_chunks

026 agents
027 agent_capabilities
028 tools
029 tool_capabilities
030 agent_runs
031 tool_runs

032 automations
033 automation_triggers
034 automation_actions

035 audit_logs

Đây là logical rollout order. Tên migration thực tế sẽ theo framework được chọn sau khi source architecture được chốt.

---

# 22. Transaction boundaries

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

# 23. Credential access boundary

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

# 24. Knowledge authorization

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

# 25. Audit requirements

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

# 26. Performance strategy

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

# 27. Backup / restore

Production database phải có:

- automated backup;
- point-in-time recovery nếu deployment hỗ trợ;
- encrypted backup;
- restore test định kỳ;
- credential encryption key backup strategy riêng;
- không lưu secret plaintext trong logs.

Backup database không thay thế key management.

---

# 28. Database security boundary

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

# 29. Core Database vs Domain Extensions

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

# 30. ERD logical summary

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
   └────────► agent_runs ─────► tool_runs ─────► tools

 users ─────► automations
                 ├────► automation_triggers
                 └────► automation_actions

                         audit_logs

---

# 31. Database V2 acceptance checklist

Schema chỉ ready for implementation khi:

- [ ] PostgreSQL được chọn.
- [ ] UUID/UUIDv7 convention được khóa.
- [ ] UTC timestamp convention được khóa.
- [ ] User/account model được khóa.
- [ ] Credential boundary được khóa.
- [ ] Role/permission model được khóa.
- [ ] Role-to-permission mapping được khóa.
- [ ] Account grant model được khóa.
- [ ] Resource authorization được khóa.
- [ ] Data Package versioning được khóa.
- [ ] Device identity tách khỏi User.
- [ ] Observation/Event/Activity tách biệt.
- [ ] Conversation/Memory/Knowledge tách biệt.
- [ ] Qdrant mapping được xác định.
- [ ] Agent/Tool/Run trace được xác định.
- [ ] Audit model được xác định.
- [ ] FK strategy được xác định.
- [ ] Unique constraints được xác định.
- [ ] Index strategy được xác định.
- [ ] Delete behavior được review.
- [ ] Migration order được review.
- [ ] Runtime authorization test cases được chuẩn bị.

---

# 32. Runtime verification bắt buộc

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

# 33. Chốt trạng thái

DATABASE_V2_DETAILED.md là schema design blueprint, chưa phải implementation.

Schema V2 đã được review nội bộ theo các dependency và authorization invariants; các điểm bắt buộc gồm role-to-permission mapping, resource-to-account binding và migration FK order.

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
