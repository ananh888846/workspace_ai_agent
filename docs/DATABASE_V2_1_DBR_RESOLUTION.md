# Database V2.1 — DBR Design Resolution

> Ngày cập nhật: 2026-09-21  
> Không sửa ngược migration 001 → 045; thay đổi schema chỉ qua migration hậu V2.1.

## 1. Resolution matrix

| Finding | Resolution | Migration | Status |
|---|---|---|---|
| DBR-001 Event user/org | ACCEPT FIX | 046 | RESOLVED FOR MIGRATION |
| DBR-002 Activity Session user/org | ACCEPT FIX | 046 | RESOLVED FOR MIGRATION |
| DBR-003 Activity user/org | ACCEPT FIX | 046 | RESOLVED FOR MIGRATION |
| DBR-004 Agent Run/Conversation ownership | ACCEPT FIX | 047 | RESOLVED FOR MIGRATION |
| DBR-005 Tool Run/account context | ACCEPT FIX | 048 | RESOLVED FOR MIGRATION |
| DBR-006 Audit Log/account context | ACCEPT FIX | 049 | RESOLVED FOR MIGRATION |
| DBR-007 Resource uniqueness | ACCEPT FIX | 050 | RESOLVED FOR MIGRATION |

## 2. DBR-001 → DBR-003

Event, Activity Session và Activity enforce `(organization_id,user_id) → organization_members(organization_id,user_id)`. Nullability không thay đổi.

## 3. DBR-004

Conversation vẫn user-owned. Thêm `UNIQUE(id,user_id)` và Agent Run dùng composite FK `(conversation_id,user_id) → conversations(id,user_id)`.

## 4. DBR-005 — Tool Run execution account

`tool_runs` ghi `organization_id` và `user_id` từ `agent_runs`, cùng optional `account_grant_id`. Account context là direct ownership hoặc active delegated grant. Trigger kiểm tra organization, grantee, account, status/revocation và thời hạn tại `agent_runs.started_at`.

## 5. DBR-006 — Audit Log account context

`audit_logs` bổ sung `account_grant_id`. Khi `account_id` có giá trị, `organization_id` và `user_id` bắt buộc có. Account phải owned trực tiếp hoặc delegated hợp lệ tại `created_at`.

## 6. DBR-007 — Resource identity

Account-backed: `(provider,user_account_id,resource_type,external_id)`. Local: `(organization_id,provider,resource_type,external_id)` khi `user_account_id IS NULL`. Migration 050 dùng hai partial unique indexes.

## 7. Migration hậu V2.1

- [046_harden_activity_event_user_tenant_integrity.sql](../database/migrations/046_harden_activity_event_user_tenant_integrity.sql)
- [047_harden_conversation_owner_integrity.sql](../database/migrations/047_harden_conversation_owner_integrity.sql)
- [048_bind_tool_run_account_context.sql](../database/migrations/048_bind_tool_run_account_context.sql)
- [049_bind_audit_account_context.sql](../database/migrations/049_bind_audit_account_context.sql)
- [050_lock_resource_identity_semantics.sql](../database/migrations/050_lock_resource_identity_semantics.sql)

## 8. Acceptance bắt buộc

- Cross-org Event/Activity Session/Activity user → REJECT.
- Agent Run user A → Conversation user B → REJECT; same-user → ACCEPT.
- Tool Run owned account → ACCEPT; active delegated account → ACCEPT; invalid/expired/revoked/wrong-org grant → REJECT.
- Audit owned account → ACCEPT; active delegated account → ACCEPT; invalid delegated account → REJECT.
- Account-backed duplicate identity → REJECT.
- Local duplicate within same organization → REJECT.
- Same local identity across different organizations → ACCEPT.
- NULL optional values remain valid.

## 9. Gate

DBR-001 → DBR-007: **CLOSED**.

Migrations 046 → 050 đã được chạy thực tế trên PostgreSQL 18.6. Acceptance AT-053 → AT-065 đạt **13/13 PASS** và transaction kết thúc bằng `ROLLBACK`. Runtime catalog verification RV-001 → RV-014 đạt **14/14 PASS** và transaction kết thúc bằng `ROLLBACK`.

**Database V2.1 Post-Implementation Review Gate: CLOSED.** Không sửa ngược Migration 001 → 045; các finding DBR-001 → DBR-007 đã được giải quyết bằng migration 046 → 050.
