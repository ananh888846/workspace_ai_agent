# Database V2.1 — DBR Design Resolution

> Ngày: 2026-09-21  
> Phạm vi: DBR-001 → DBR-007 từ Post-Implementation Review.  
> Nguyên tắc: không sửa ngược migration 001 → 045; thay đổi schema chỉ qua migration hậu V2.1.

## 1. Resolution matrix

| Finding | Resolution | Action |
|---|---|---|
| DBR-001 Event user/org | ACCEPT FIX | Composite FK (organization_id,user_id) → organization_members |
| DBR-002 Activity Session user/org | ACCEPT FIX | Composite FK (organization_id,user_id) → organization_members |
| DBR-003 Activity user/org | ACCEPT FIX | Composite FK (organization_id,user_id) → organization_members |
| DBR-004 Agent Run/Conversation ownership | ACCEPT FIX | Add UNIQUE(id,user_id) to conversations; composite FK from agent_runs |
| DBR-005 Tool Run/account context | DEFER | Contract decision required |
| DBR-006 Audit Log/account context | DEFER | Contract decision required |
| DBR-007 Resource uniqueness | DEFER | Provider identity decision required |

## 2. DBR-001 → DBR-003

Event, Activity Session và Activity đều có organization_id. user_id nullable phải được enforce là member của chính organization.

Migration hậu V2.1 sẽ thay FK đơn user_id → users bằng composite FK:
(organization_id,user_id) → organization_members(organization_id,user_id).

Không đổi nullability.

## 3. DBR-004

Conversation vẫn user-owned; không thêm organization_id.

Để Agent Run không thể tham chiếu conversation của user khác:

- thêm UNIQUE(id,user_id) vào conversations;
- thay FK agent_runs.conversation_id → conversations.id bằng composite FK:
  (conversation_id,user_id) → conversations(id,user_id).

Điều này giữ nguyên Decision 009/033.

## 4. DBR-005 — Deferred

tool_runs.account_id cần chốt semantics: account của user thực hiện Agent Run, account được grant, hay account do execution context chọn.

Không suy đoán và không sửa schema trước khi có architecture decision.

## 5. DBR-006 — Deferred

audit_logs.account_id có thể là account do user sở hữu hoặc account được grant/execution sử dụng.

Chưa thêm composite FK account/user cho tới khi semantics được khóa.

## 6. DBR-007 — Deferred

Current resource identity:
UNIQUE(provider,user_account_id,resource_type,external_id)

Chưa tự thêm organization_id. Cần chốt provider/resource identity semantics trước khi thay đổi uniqueness.

## 7. Migration hậu V2.1 dự kiến

046_harden_activity_event_user_tenant_integrity.sql xử lý DBR-001 → DBR-003.

047_harden_conversation_owner_integrity.sql xử lý DBR-004.

DBR-005 → DBR-007 chỉ tạo migration sau khi Decision tương ứng được Accepted.

## 8. Acceptance bắt buộc

- Cross-org Event user → REJECT.
- Cross-org Activity Session user → REJECT.
- Cross-org Activity user → REJECT.
- Agent Run user A → Conversation user B → REJECT.
- Same-user Conversation → ACCEPT.
- NULL optional values vẫn hoạt động đúng.

## 9. Gate

DBR-001 → DBR-004: RESOLVED FOR MIGRATION.

DBR-005 → DBR-007: OPEN — REQUIRES ARCHITECTURE DECISION.

Database V2.1 overall post-implementation gate vẫn OPEN cho đến khi migration hậu V2.1 và các deferred decisions hoàn tất.
