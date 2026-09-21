# Migration 011 → 020 — DDL Design V2.1

> Design gate update: schema review complete; SQL production will be created only after the tenant/session integrity corrections below.
>
> Source of truth: DATABASE_V2_DETAILED.md, MIGRATION_CONTRACT_V2.md, ERD_V2.md.

## 1. Phạm vi

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

Nhóm này khóa Resource, Data Package, Device và Session foundation.

## 2. Migration 011 — resources

Tenant-scoped resource bắt buộc có organization_id.

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| organization_id | UUID | NO | — | FK, INDEX |
| parent_resource_id | UUID | YES | NULL | composite FK, INDEX |
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

Required keys:
- UNIQUE(id, organization_id)
- UNIQUE(provider, user_account_id, resource_type, external_id)

Required integrity:
- organization_id → organizations.id
- owner_user_id → users.id
- user_account_id → user_accounts.id when not NULL
- (parent_resource_id, organization_id) → resources(id, organization_id) when parent not NULL

Provider/account consistency must be enforced by DB constraint/trigger or equivalent database mechanism approved by the contract; application-only validation is insufficient.

Delete:
- parent/resource/account/owner relationships use RESTRICT.
- Resource hierarchy deletion must be explicit; no broad cascade.

## 3. Migration 012 — resource_permissions

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| resource_id | UUID | NO | — | FK, INDEX |
| user_id | UUID | NO | — | FK, INDEX |
| action | VARCHAR(100) | NO | — | |
| effect | VARCHAR(16) | NO | allow | |
| created_at | TIMESTAMPTZ | NO | now() | |
| expires_at | TIMESTAMPTZ | YES | NULL | INDEX |

UNIQUE(resource_id, user_id, action).

FK resource_id → resources.id and user_id → users.id.

CHECK: expires_at >= created_at when expires_at is present.

Delete policy: RESTRICT for resource/user; permission records are authorization history, not disposable mapping data.

## 4. Migration 013 — data_packages

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| organization_id | UUID | NO | — | FK, INDEX |
| owner_user_id | UUID | NO | — | composite FK, INDEX |
| name | VARCHAR(255) | NO | — | |
| description | TEXT | YES | NULL | |
| package_type | VARCHAR(64) | NO | — | INDEX |
| status | VARCHAR(32) | NO | active | INDEX |
| created_at | TIMESTAMPTZ | NO | now() | |
| updated_at | TIMESTAMPTZ | NO | now() | |

Required:
- UNIQUE(id, organization_id)
- organization_id → organizations.id
- (organization_id, owner_user_id) → organization_members(organization_id, user_id)

Package owner must be an organization member. DELETE uses RESTRICT.

## 5. Migration 014 — data_package_versions

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| organization_id | UUID | NO | — | FK |
| data_package_id | UUID | NO | — | composite FK, INDEX |
| version | INTEGER | NO | — | |
| status | VARCHAR(32) | NO | draft | INDEX |
| created_by | UUID | NO | — | FK, INDEX |
| created_at | TIMESTAMPTZ | NO | now() | |

Required:
- UNIQUE(data_package_id, version)
- UNIQUE(id, organization_id)
- (data_package_id, organization_id) → data_packages(id, organization_id)
- created_by → users.id

CHECK version > 0.

Delete package/version uses RESTRICT because package version is an authorization/data lineage boundary.

## 6. Migration 015 — data_package_resources

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| organization_id | UUID | NO | — | FK, INDEX |
| package_version_id | UUID | NO | — | composite FK, INDEX |
| resource_id | UUID | NO | — | composite FK, INDEX |
| access_mode | VARCHAR(32) | NO | read | |

Required:
- UNIQUE(package_version_id, resource_id)
- UNIQUE(id, organization_id)
- (package_version_id, organization_id) → data_package_versions(id, organization_id)
- (resource_id, organization_id) → resources(id, organization_id)

This is the database-level package/resource tenant barrier. A resource from another organization must be rejected.

Delete policy: CASCADE from package version/resource mapping only as approved mapping-table behavior.

## 7. Migration 016 — data_package_grants

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| organization_id | UUID | NO | — | FK, INDEX |
| package_version_id | UUID | NO | — | composite FK, INDEX |
| user_id | UUID | NO | — | composite FK, INDEX |
| permission | VARCHAR(100) | NO | — | |
| starts_at | TIMESTAMPTZ | YES | NULL | |
| expires_at | TIMESTAMPTZ | YES | NULL | INDEX |
| created_at | TIMESTAMPTZ | NO | now() | |
| revoked_at | TIMESTAMPTZ | YES | NULL | |

Required:
- UNIQUE(package_version_id, user_id, permission)
- UNIQUE(id, organization_id)
- (package_version_id, organization_id) → data_package_versions(id, organization_id)
- (organization_id, user_id) → organization_members(organization_id, user_id)

CHECK expires_at >= starts_at when both are present.

Grant revocation uses revoked_at/status semantics; do not delete to erase authorization history. RESTRICT by default.

## 8. Migration 017 — devices

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| organization_id | UUID | NO | — | FK, INDEX |
| resource_id | UUID | YES | NULL | composite FK, INDEX |
| device_uuid | UUID | NO | — | UNIQUE |
| device_type | VARCHAR(64) | NO | — | INDEX |
| name | VARCHAR(255) | YES | NULL | |
| status | VARCHAR(32) | NO | active | INDEX |
| firmware_version | VARCHAR(100) | YES | NULL | |
| created_at | TIMESTAMPTZ | NO | now() | |
| updated_at | TIMESTAMPTZ | NO | now() | |
| last_seen_at | TIMESTAMPTZ | YES | NULL | INDEX |

Required:
- UNIQUE(id, organization_id)
- organization_id → organizations.id
- (resource_id, organization_id) → resources(id, organization_id) when resource_id is not NULL

Device is an identity separate from User. Device resource binding cannot cross organizations.

Delete resource/device relationship: RESTRICT.

## 9. Migration 018 — user_sessions

Session is tenant-bound so a session cannot bind a user from one organization to a device from another organization.

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| organization_id | UUID | NO | — | FK, INDEX |
| user_id | UUID | NO | — | composite FK, INDEX |
| session_token_hash | VARCHAR(255) | NO | — | UNIQUE |
| device_id | UUID | YES | NULL | composite FK, INDEX |
| ip_address | INET | YES | NULL | |
| user_agent | TEXT | YES | NULL | |
| started_at | TIMESTAMPTZ | NO | now() | |
| expires_at | TIMESTAMPTZ | NO | — | INDEX |
| last_activity_at | TIMESTAMPTZ | YES | NULL | INDEX |
| revoked_at | TIMESTAMPTZ | YES | NULL | |
| created_at | TIMESTAMPTZ | NO | now() | |

Required:
- organization_id → organizations.id
- (organization_id, user_id) → organization_members(organization_id, user_id)
- (device_id, organization_id) → devices(id, organization_id) when device_id is present
- session_token_hash UNIQUE

Security:
- never store raw session token;
- session lookup uses hash;
- revoked/expired sessions must fail authentication.

CHECK expires_at >= started_at.

Delete policy: RESTRICT for organization/user/device.

## 10. Migration 019 — device_users

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| organization_id | UUID | NO | — | PK, FK, INDEX |
| device_id | UUID | NO | — | PK, composite FK |
| user_id | UUID | NO | — | PK, composite FK |
| relationship | VARCHAR(64) | NO | — | |
| status | VARCHAR(32) | NO | active | INDEX |
| created_at | TIMESTAMPTZ | NO | now() | |

PK: (organization_id, device_id, user_id).

Required tenant FKs:
- (device_id, organization_id) → devices(id, organization_id)
- (organization_id, user_id) → organization_members(organization_id, user_id)

Because Device is tenant-scoped, cross-organization device-user binding is rejected by database-level composite FKs.

Mapping delete policy: CASCADE from device/user into mapping is allowed.

## 11. Migration 020 — device_capabilities

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| device_id | UUID | NO | — | FK, INDEX |
| capability | VARCHAR(100) | NO | — | |
| enabled | BOOLEAN | NO | true | |
| config | JSONB | NO | {} | |

UNIQUE(device_id, capability).

FK device_id → devices.id.

Delete policy: CASCADE from device to capability mapping.

Capability configuration is not a permission grant. Runtime authorization remains separate.

## 12. Dependency order

011 resources
→ 012 resource_permissions
→ 013 data_packages
→ 014 data_package_versions
→ 015 data_package_resources
→ 016 data_package_grants
→ 017 devices
→ 018 user_sessions
→ 019 device_users
→ 020 device_capabilities

Important dependencies:
- resources needs organizations, users, user_accounts.
- packages need organization_members.
- package resources need resources + package versions.
- package grants need package versions + organization_members.
- devices need resources + organizations.
- sessions need users + devices.
- device mappings/capabilities need devices.

## 13. Acceptance tests

AT-011 Resource parent from another organization → REJECT.
AT-012 Resource account ownership/provider mismatch → REJECT.
AT-013 Package owner not organization member → REJECT.
AT-014 Package version referencing another organization → REJECT.
AT-015 Package resource from another organization → REJECT.
AT-016 Package grant user from another organization → REJECT.
AT-017 Device resource from another organization → REJECT.
AT-018 Session references nonexistent user/device → FK REJECT.
AT-019 Session references user/device across organizations → composite FK REJECT.
AT-020 Expired/invalid session temporal state → CHECK REJECT.
AT-021 Device capability duplicate → UNIQUE REJECT.

## 14. Implementation gate

- [x] Resources are mandatory tenant-scoped.
- [x] Resource parent hierarchy uses composite tenant FK.
- [x] Resource/account relationship is explicit.
- [x] Data Package and all child entities carry organization_id.
- [x] Package/resource cross-tenant insertion is DB-blocked.
- [x] Package grant membership is DB-blocked across tenants.
- [x] Devices are tenant-scoped and resource binding is DB-blocked across tenants.
- [x] Sessions are created only after users/devices.
- [x] Session token is hashed, never plaintext.
- [x] Mapping tables have explicit CASCADE only where approved.
- [x] Business/history authorization relationships use RESTRICT.
- [x] No provider API calls or runtime code are introduced.
- [x] No production credentials or user data are seeded.

Kết luận: Migration 011 → 020 đã đủ thiết kế DDL để làm input cho bước SQL implementation, sau khi composite tenant constraint cho device_users được biểu diễn bằng target key tương ứng trong schema SQL.


## 15. Pre-SQL review correction — 2026-09-21 10:00:00 +07:00

- user_sessions is explicitly tenant-scoped with organization_id so a session cannot cross-bind a user and device across organizations.
- device_users now carries organization_id and uses composite tenant FKs to both devices and organization_members.
- resources must enforce account ownership with composite FK (user_account_id, owner_user_id) → user_accounts(id, user_id), and provider/account compatibility at database level.
- SQL 011 → 020 will be generated only after these corrections are reflected in the source-of-truth contract.
