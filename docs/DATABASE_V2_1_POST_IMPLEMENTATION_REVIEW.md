# Workspace AI Agent — DATABASE V2.1 Post-Implementation Review

> Review phạm vi: Migration 001 → 045 và các contract/database docs trên branch `main`.
>
> Ngày review: 2026-09-21
>
> Trạng thái: **STATIC REVIEW COMPLETED — ACTIONS OPEN**
>
> Lưu ý: review này đối chiếu source SQL trên GitHub với schema contract và acceptance evidence đã ghi nhận. Đây chưa phải là introspection trực tiếp từ database runtime hiện tại.

## 1. Kết luận

Production SQL Migration 001 → 045 đã được tạo và các acceptance gate hiện có đều đã PASS theo changelog/decision.

Tuy nhiên, static post-implementation review phát hiện một số quan hệ tenant/user chưa được database enforce ở mức mạnh như contract V2.1 đang mô tả. Vì vậy **chưa nên tuyên bố Database V2.1 là hoàn toàn đóng về tenant-integrity** cho đến khi các finding dưới đây được quyết định và xử lý.

Không sửa production migration 001 → 045 trực tiếp trong review này. Các thay đổi schema tiếp theo phải đi qua migration mới.

## 2. Findings

### DBR-001 — Event user chưa enforce cùng organization

**File:** `database/migrations/022_create_events.sql`

`events.organization_id` là tenant-scoped nhưng `events.user_id` chỉ FK tới `users(id)`:

```sql
FOREIGN KEY (user_id) REFERENCES users(id)
```

Điều này cho phép về mặt DB một Event thuộc Org A tham chiếu User là member của Org B hoặc không thuộc Org A.

**Đề xuất migration tiếp theo:**

- giữ `user_id` nullable;
- thêm `UNIQUE(id, organization_id)` đã có;
- dùng composite FK:
  `(organization_id, user_id) → organization_members(organization_id, user_id)`.

**Mức:** Tenant-integrity gap.

---

### DBR-002 — Activity Session user chưa enforce cùng organization

**File:** `database/migrations/023_create_activity_sessions.sql`

`activity_sessions.organization_id` là tenant-scoped nhưng `user_id` chỉ FK tới `users(id)`.

**Đề xuất:**

`(organization_id, user_id) → organization_members(organization_id, user_id)`.

**Mức:** Tenant-integrity gap.

---

### DBR-003 — Activity user chưa enforce cùng organization

**File:** `database/migrations/024_create_activities.sql`

Tương tự Activity Session: `activities.user_id` chỉ tham chiếu `users(id)`.

**Đề xuất:**

`(organization_id, user_id) → organization_members(organization_id, user_id)`.

**Mức:** Tenant-integrity gap.

---

### DBR-004 — Agent Run → Conversation chưa enforce user ownership

**File:** `database/migrations/035_create_agent_runs.sql`

Agent Run có `organization_id + user_id`, nhưng `conversation_id` chỉ FK tới `conversations(id)`.

Trong khi Conversation hiện là user-owned và không mang `organization_id`. Vì vậy database chưa đảm bảo conversation được dùng bởi Agent Run thuộc đúng user.

**Đề xuất contract:**

- giữ Conversation user-owned theo Decision 009/033;
- bổ sung unique target `conversations(id, user_id)`;
- Agent Run dùng composite FK:
  `(conversation_id, user_id) → conversations(id, user_id)`.

Không cần thêm `organization_id` vào conversations chỉ để giải quyết vấn đề này.

**Mức:** Ownership-integrity gap.

---

### DBR-005 — Tool Run → Account chưa có ownership/tenant context

**File:** `database/migrations/036_create_tool_runs.sql`

`tool_runs.account_id` chỉ FK tới `user_accounts(id)`. Tool Run kế thừa tenant qua `agent_run_id`, nhưng bản thân Tool Run không có `organization_id` hoặc `user_id` để database chứng minh account đang được dùng thuộc đúng execution context.

Đây là vấn đề cần chốt ở contract vì external account hiện được model theo User, còn Account Grant lại tenant-scoped.

**Đề xuất review tiếp theo:**

- xác định Tool Run account phải là account của Agent Run user hay có thể là account được grant;
- nếu cần DB-level ownership, bổ sung context columns/composite target hoặc thiết kế execution-account binding riêng;
- không dùng application-only check nếu contract yêu cầu DB tenant isolation.

**Mức:** Authorization/execution-boundary gap — cần decision trước migration.

---

### DBR-006 — Audit Log → Account chưa có tenant/user ownership binding

**File:** `database/migrations/045_create_audit_logs.sql`

`audit_logs.account_id` chỉ FK tới `user_accounts(id)`.

Trong khi Audit Log có `organization_id` và `user_id`. Database chưa chứng minh account thuộc user/org của audit record.

**Đề xuất:**

- chốt semantics khi `account_id IS NOT NULL`;
- có thể dùng `(account_id, user_id) → user_accounts(id, user_id)`;
- nếu audit account có thể đại diện account được grant, cần một execution/access binding rõ hơn thay vì suy ra từ owner.

**Mức:** Audit authorization-context gap.

---

### DBR-007 — Resource uniqueness chưa tenant-scoped

**File:** `database/migrations/011_create_resources.sql`

Resource có `organization_id`, nhưng uniqueness chính được thiết kế theo provider/account/type/external ID và không chứa organization.

Điều này cần được chốt theo provider contract: cùng một external resource có thể được nhìn thấy bởi nhiều organization thông qua cùng account, hoặc resource identity có thể phải độc lập theo tenant.

**Đề xuất:**

- nếu resource identity là tenant-local: uniqueness phải bao gồm `organization_id`;
- nếu resource identity là provider-global/account-global: giữ current key nhưng ghi rõ semantics trong contract.

Không tự sửa trước khi provider identity semantics được chốt.

**Mức:** Identity/uniqueness contract gap.

## 3. Những phần đã xác nhận tốt

Static review xác nhận các boundary quan trọng sau đang được triển khai nhất quán:

- Resource hierarchy dùng composite tenant FK.
- Data Package/version/resource/grant dùng composite tenant FK.
- Device → Resource dùng composite tenant FK.
- User Session → organization member/device cùng tenant.
- Device User → device/member cùng tenant.
- Task creator/assignee/parent/resource/event cùng tenant.
- Agent → Organization và A2A Agent Task/Permission/Message cùng tenant.
- Automation → Trigger/Action cùng tenant.
- Anomaly → user/device/resource/event/activity/task cùng tenant.
- Anomaly Evidence dùng explicit source FKs và exactly-one source CHECK.
- Audit Log append-only và có metadata secret-key guard.
- Qdrant mapping qua Knowledge Chunk không được dùng làm authorization source.

## 4. Acceptance status

Các gate đã ghi nhận:

| Gate | Result |
|---|---|
| 001 → 010 | PASS — 8/8 |
| 011 → 020 | PASS — 12/12 |
| 021 → 030 | PASS — 10/10 |
| 031 → 033 | PASS — 4/4 |
| 011 → 033 Integration | PASS — 6/6 |
| 034 → 045 | PASS — 12/12 |

Acceptance PASS chứng minh các case đã được test, nhưng không thay thế static schema review. Các finding DBR-001 → DBR-007 cần acceptance bổ sung nếu schema contract được sửa.

## 5. Quy tắc xử lý tiếp theo

1. Không chỉnh sửa ngược Migration 001 → 045.
2. Chốt semantics cho DBR-004 → DBR-007.
3. Tạo migration hậu V2.1 cho các thay đổi được duyệt.
4. Bổ sung acceptance tests cho từng finding.
5. Chạy lại integration/tenant verification trên PostgreSQL 18.6.
6. Sau khi PASS mới chuyển trạng thái review từ ACTIONS OPEN sang CLOSED.

## 6. Runtime verification còn thiếu

Review này chưa xác nhận trực tiếp database runtime hiện tại bằng `pg_catalog`/`information_schema`.

Khi thực hiện runtime verification, cần kiểm tra tối thiểu:

- 45 bảng tồn tại đúng tên;
- PK/UNIQUE/FK/CHECK thực tế khớp migration;
- composite FK target keys tồn tại;
- indexes tồn tại;
- audit triggers tồn tại và enabled;
- không có bảng/constraint/index ngoài contract ngoài những thay đổi được ghi nhận;
- migration application order đúng 001 → 045.

**Review gate: CLOSED.** DBR-001 → DBR-007 đã được giải quyết bằng Migration 046 → 050.
