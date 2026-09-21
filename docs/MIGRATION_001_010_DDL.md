# Migration 001 → 010 — DDL Design V2.1

> Design only. Chưa phải SQL production và chưa chạy database thật.
>
> Source of truth: DATABASE_V2_DETAILED.md, MIGRATION_CONTRACT_V2.md, ERD_V2.md.

## 1. Phạm vi

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

Nguyên tắc: migration sau chỉ tham chiếu bảng đã tồn tại; tenant integrity phải được enforce ở database; không có provider API call/application logic trong migration; credential thật không được seed.

## 2. Migration 001 — organizations

Table: organizations

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| name | VARCHAR(255) | NO | — | |
| organization_type | VARCHAR(64) | NO | — | INDEX |
| status | VARCHAR(32) | NO | active | INDEX |
| metadata | JSONB | NO | {} | |
| created_at | TIMESTAMPTZ | NO | now() | INDEX |
| updated_at | TIMESTAMPTZ | NO | now() | |

Không FK ngược. Không hard-code status enum bằng CHECK khi vocabulary application chưa khóa.

## 3. Migration 002 — users

Table: users

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| name | VARCHAR(200) | NO | — | |
| email | VARCHAR(320) | YES | NULL | UNIQUE khi có giá trị |
| phone | VARCHAR(32) | YES | NULL | |
| status | VARCHAR(32) | NO | active | INDEX |
| created_at | TIMESTAMPTZ | NO | now() | INDEX |
| updated_at | TIMESTAMPTZ | NO | now() | |

User không bị giới hạn vào một organization duy nhất.

## 4. Migration 003 — organization_members

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| organization_id | UUID | NO | — | PK, FK |
| user_id | UUID | NO | — | PK, FK |
| member_role | VARCHAR(64) | NO | member | INDEX |
| status | VARCHAR(32) | NO | active | INDEX |
| joined_at | TIMESTAMPTZ | NO | now() | |
| created_at | TIMESTAMPTZ | NO | now() | |

PK: (organization_id, user_id)

FK:
- organization_id → organizations.id
- user_id → users.id

Đây là target composite key cho tenant FK về membership. Không cascade mặc định vì membership là authorization boundary.

## 5. Migration 004 — user_accounts

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

Required:
- FK user_id → users.id
- UNIQUE(provider, external_account_id)
- UNIQUE(id, user_id)

UNIQUE(id, user_id) là target cho composite FK account_grants(user_account_id, owner_user_id).

Delete policy: RESTRICT. Không cascade credential/grant từ account.

## 6. Migration 005 — account_credentials

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
- encrypted only;
- không plaintext;
- không log;
- không prompt;
- không AgentContext;
- không audit payload;
- resolver chỉ được gọi sau Authorization ALLOW.

FK user_account_id → user_accounts.id, ON DELETE RESTRICT.

## 7. Migration 006 — roles

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| name | VARCHAR(100) | NO | — | UNIQUE |
| description | TEXT | YES | NULL | |
| created_at | TIMESTAMPTZ | NO | now() | |
| updated_at | TIMESTAMPTZ | NO | now() | |

Role là application authorization concept, không đồng nhất với organization membership.

## 8. Migration 007 — permissions

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| resource | VARCHAR(100) | NO | — | |
| action | VARCHAR(100) | NO | — | |
| description | TEXT | YES | NULL | |
| created_at | TIMESTAMPTZ | NO | now() | |

UNIQUE(resource, action).

Reference permissions như drive.read, drive.write, home.control thuộc seed/application contract riêng, không bắt buộc trong schema migration.

## 9. Migration 008 — user_roles

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| user_id | UUID | NO | — | PK, FK |
| role_id | UUID | NO | — | PK, FK |
| created_at | TIMESTAMPTZ | NO | now() | |

PK: (user_id, role_id)

FK:
- user_id → users.id
- role_id → roles.id

Đây là mapping thuần quan hệ: CASCADE từ User/Role xuống mapping. Tạo index role_id để reverse lookup.

## 10. Migration 009 — role_permissions

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| role_id | UUID | NO | — | PK, FK |
| permission_id | UUID | NO | — | PK, FK |
| created_at | TIMESTAMPTZ | NO | now() | |

PK: (role_id, permission_id)

FK:
- role_id → roles.id
- permission_id → permissions.id

Mapping thuần quan hệ: CASCADE từ Role/Permission xuống mapping. Tạo index permission_id.

## 11. Migration 010 — account_grants

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

Required keys:
- PK id
- UNIQUE(id, organization_id)

Required FKs:
1. organization_id → organizations.id
2. (organization_id, owner_user_id) → organization_members(organization_id, user_id)
3. (organization_id, grantee_user_id) → organization_members(organization_id, user_id)
4. (user_account_id, owner_user_id) → user_accounts(id, user_id)

Điểm quan trọng: không được thay composite FK #4 bằng hai FK riêng, vì hai FK riêng vẫn cho phép account thuộc User A nhưng owner_user_id là User B.

Account grant là tenant-scoped. Revoke dùng status/revoked_at, không xóa để thay thế lịch sử. Các relationship dùng RESTRICT.

CHECK:
- expires_at >= starts_at khi cả hai khác NULL.

Indexes:
- organization_id
- owner_user_id
- grantee_user_id
- user_account_id
- status
- expires_at

## 12. Dependency graph

001 organizations
  ↓
003 organization_members ← 002 users
  ↓
010 account_grants ← 004 user_accounts ← 005 account_credentials
                       ↑
002 users

006 roles → 008 user_roles
007 permissions → 009 role_permissions

Thứ tự migration contract vẫn là 001 → 010.

## 13. Acceptance tests

AT-001: owner thuộc Org A nhưng grant ghi Org B → REJECT.
AT-002: grantee không thuộc organization ghi trên grant → REJECT.
AT-003: account thuộc User A nhưng owner_user_id = User B → REJECT.
AT-004: owner, grantee cùng Org và account đúng owner → INSERT thành công.
AT-005: expires_at < starts_at → REJECT.
AT-006: role/permission tồn tại → mapping thành công.
AT-007: role không tồn tại → FK REJECT.
AT-008: permission không tồn tại → FK REJECT.

## 14. Implementation gate

- [x] 001 → 010 không có dependency cycle.
- [x] organization_members có composite PK.
- [x] user_accounts có UNIQUE(id, user_id).
- [x] account_grants có UNIQUE(id, organization_id).
- [x] Account Grant có đủ 4 FK bắt buộc.
- [x] Tenant isolation không phụ thuộc application-only checks.
- [x] Credential không có plaintext contract.
- [x] Mapping tables có CASCADE phù hợp.
- [x] Authorization/history dùng RESTRICT.
- [x] Temporal CHECK đã khóa.
- [x] Index contract đã phản ánh.
- [x] Không seed credential/production data.

Kết luận: Migration 001 → 010 đã đủ thiết kế để viết SQL. Chưa phải migration production cho tới khi SQL được tạo và chạy qua clean PostgreSQL acceptance suite.
