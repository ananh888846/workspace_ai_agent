# Migration 041 → 045 — DDL Design V2.1

> Design only. Chưa phải SQL production và chưa chạy database thật.
>
> Source of truth: `DATABASE_V2_DETAILED.md`, `MIGRATION_CONTRACT_V2.md`, `ERD_V2.md`.
>
> Nhóm này hoàn tất Automation, Anomaly/Evidence và Audit.

## 1. Phạm vi

041 automation_triggers  
042 automation_actions  
043 anomalies  
044 anomaly_evidence  
045 audit_logs

## 2. Migration 041 — automation_triggers

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| automation_id | UUID | NO | — | FK, INDEX |
| event_type | VARCHAR(100) | NO | — | INDEX |
| conditions | JSONB | NO | {} | |

Required:
- `automation_id → automations.id`.
- `conditions` chỉ chứa điều kiện trigger; không chứa credential/token.
- Automation trigger chỉ tạo execution candidate; không tự bypass Authorization.
- Trigger evaluation phải chạy trong owner/organization authorization context khi resource/account access liên quan.

Indexes:
- `automation_id`.
- `(event_type, automation_id)`.

Delete policy: RESTRICT theo automation lifecycle contract; không xóa lịch sử execution chỉ vì trigger definition thay đổi.

## 3. Migration 042 — automation_actions

| Column | Type | Null | Default | Key |
|---|---|---:|---|---|
| id | UUID | NO | UUIDv7 | PK |
| automation_id | UUID | NO | — | FK, INDEX |
| action_type | VARCHAR(100) | NO | — | INDEX |
| config | JSONB | NO | {} | |

Required:
- `automation_id → automations.id`.
- `config` chỉ lưu action configuration, không lưu credential.
- Action execution phải đi qua Authorization/Tool boundary.
- `action_type` không được xem như permission; actual capability/action/resource authorization vẫn phải được kiểm tra khi chạy.
- Provider-specific account/credential chỉ được resolve sau ALLOW.

Indexes:
- `automation_id`.
- `(action_type, automation_id)`.

Delete policy: RESTRICT theo automation lifecycle contract.

## 4. Migration 043 — anomalies

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

Required:
- `organization_id → organizations.id`.
- Optional user/device/resource/event/activity/task references → corresponding tables.
- Every tenant-scoped reference must match `anomalies.organization_id` at DB level through composite FK/equivalent constraint.
- CHECK `confidence BETWEEN 0 AND 1` when present.
- CHECK `resolved_at >= detected_at` when resolved_at is present.
- Anomaly is evidence-backed inference; severity/status do not prove cause or wrongdoing.

Indexes:
- `(organization_id, detected_at)`.
- `(organization_id, status, detected_at)`.
- `(organization_id, severity, detected_at)`.
- `(organization_id, anomaly_type, detected_at)`.
- Optional source indexes for event/activity/task/resource/device.

Delete policy: RESTRICT. Anomaly history must not disappear with source facts.

## 5. Migration 044 — anomaly_evidence

Evidence links an anomaly to a source fact/entity.

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

Source types locked for V2.1:
- `observation`
- `event`
- `activity_session`
- `activity`
- `task`
- `device`
- `resource`

Required:
- `anomaly_id → anomalies.id`.
- `source_id` must resolve to the entity represented by `source_type`.
- Source must belong to the same organization as the anomaly.
- CHECK `weight BETWEEN 0 AND 1` when present.
- `evidence_role` is semantic metadata; it does not itself establish truth.

Important implementation gate:
- PostgreSQL cannot express the polymorphic `source_type + source_id` relationship as one ordinary FK.
- Production implementation must use an explicit DB-level strategy: separate nullable FK columns per source type, a normalized evidence-source mapping table, or another equivalent constraint/trigger strategy.
- Application-only lookup is not sufficient for the tenant integrity requirement.

Indexes:
- `(anomaly_id, created_at)`.
- `(source_type, source_id)`.
- `(anomaly_id, source_type, source_id)` for duplicate/evidence lookup.

Delete policy: RESTRICT.

## 6. Migration 045 — audit_logs

Audit log là immutable security trace cho operation nhạy cảm.

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

Required:
- `request_id` là correlation identifier.
- Optional FK references phải trỏ đúng entity.
- Nếu `organization_id` khác NULL, tenant-scoped device/resource/package/account references phải cùng organization.
- Audit record không chứa access token, refresh token, API key, password, private key hoặc device secret.
- `metadata` chỉ chứa audit-safe metadata; phải có redaction policy.
- Audit row không được update/delete trong normal runtime.

Indexes:
- `(organization_id, created_at)`.
- `(organization_id, action, created_at)`.
- `(organization_id, result, created_at)`.
- `request_id`.
- `user_id, created_at`.
- `resource_id, created_at`.
- `account_id, created_at`.

Delete policy: RESTRICT / append-only. Production retention/purge phải là controlled compliance operation, không phải normal application DELETE.

## 7. Dependency order

041 automation_triggers → 042 automation_actions → 043 anomalies → 044 anomaly_evidence → 045 audit_logs

Dependency notes:
- 041/042 cần `automations`.
- 043 cần organizations/users/devices/resources/events/activities/tasks.
- 044 cần anomalies và source entities.
- 045 cần organizations/users/devices/resources/user_accounts/data_package_versions.

Không được đảo thứ tự nếu production SQL giữ các FK như contract.

## 8. Acceptance tests

AT-041 trigger referencing nonexistent Automation → FK REJECT.  
AT-042 action referencing nonexistent Automation → FK REJECT.  
AT-043 anomaly with cross-organization source reference → REJECT.  
AT-044 anomaly confidence outside [0,1] → CHECK REJECT.  
AT-045 evidence referencing nonexistent anomaly/source → FK/constraint REJECT.  
AT-046 evidence source from another organization → REJECT.  
AT-047 evidence weight outside [0,1] → CHECK REJECT.  
AT-048 audit log with invalid FK → FK REJECT.  
AT-049 audit metadata containing secret → application/security test MUST REJECT or redact.  
AT-050 normal runtime attempt to UPDATE/DELETE audit row → REJECT.

Tenant/security acceptance:
- Anomaly referencing resource/device/event/activity/task from another organization → REJECT.
- Evidence source must resolve to a valid source type and same organization.
- Audit context must never expose credential material.
- Automation action without Authorization ALLOW must not execute.
- Automation cannot be used to bypass account/resource/package authorization.
- Audit records must remain append-only during normal runtime.

## 9. Implementation gate

- [x] Automation Trigger/Action được tách khỏi Automation root.
- [x] Automation execution vẫn nằm sau Authorization/Tool boundary.
- [x] Anomaly là evidence-backed inference, không phải kết luận fraud.
- [x] Anomaly tenant scope và confidence/time checks được khóa.
- [x] Anomaly Evidence source types được liệt kê rõ.
- [x] Polymorphic Evidence source cần DB-level implementation strategy trước production SQL.
- [x] Audit schema có correlation, actor/context, result và audit-safe metadata.
- [x] Audit không chứa secret và không cho normal runtime UPDATE/DELETE.
- [x] Cross-tenant Anomaly/Evidence references phải được DB-level enforce.
- [ ] Exact Automation trigger/action execution history schema nếu cần sẽ được thiết kế ở runtime/audit phase; không tự thêm execution tables ngoài migration contract.
- [ ] Agent ↔ Organization binding từ Migration 031–040 vẫn phải được chốt trước production SQL.
- [x] No production SQL, database, provider call or runtime code is introduced.

Kết luận: Migration 041 → 045 hoàn tất DDL design contract cho Automation, Anomaly/Evidence và Audit. Sau đây có thể chuyển sang bước review toàn bộ Migration 001 → 045, chốt các implementation gates còn mở, rồi mới viết SQL production.
