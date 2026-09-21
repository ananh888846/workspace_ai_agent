# MIGRATIONS_V2_DESIGN.md

 > Trạng thái: SQL migration 001 → 010 đã được tạo và đã verify trên PostgreSQL 18.6 sạch; AT-001 → AT-008 đều PASS.
> Target PostgreSQL: 18+ (native `uuidv7()`).
> Ngày: 2026-09-21

## 1. Mục tiêu
Thiết kế 45 migration PostgreSQL theo đúng dependency của Database V2.1.
- FK được tạo sau target table.
- Composite tenant FK được enforce ở database.
- Không có dependency cycle.
- Không dùng SQLite semantics.

## 2. Quy tắc triển khai
Mỗi migration là một unit độc lập 001 → 045. Prefix cố định 001_... → 045_... để dependency order không phụ thuộc timestamp.

## 3. Thứ tự 45 migration

| # | Migration | Phụ thuộc chính |
|---:|---|---|
| 001 | organizations | — |
| 002 | users | — |
| 003 | organization_members | 001, 002 |
| 004 | user_accounts | 002 |
| 005 | account_credentials | 004 |
| 006 | roles | — |
| 007 | permissions | — |
| 008 | user_roles | 002, 006 |
| 009 | role_permissions | 006, 007 |
| 010 | account_grants | 001, 002, 003, 004 |
| 011 | resources | 001, 002, 004 |
| 012 | resource_permissions | 011, 007 |
| 013 | data_packages | 001, 002, 003 |
| 014 | data_package_versions | 013, 003 |
| 015 | data_package_resources | 014, 011 |
| 016 | data_package_grants | 014, 003 |
| 017 | devices | 001, 011 |
| 018 | user_sessions | 002, 017 |
| 019 | device_users | 002, 017 |
| 020 | device_capabilities | 017 |
| 021 | observations | 017 |
| 022 | events | 001, 002, 017, 011 |
| 023 | activity_sessions | 001, 002, 022, 011 |
| 024 | activities | 001, 002, 023 |
| 025 | tasks | 001, 002, 011, 024 |
| 026 | conversations | 002, 018 |
| 027 | messages | 026 |
| 028 | memories | 002, 026 |
| 029 | knowledge_documents | 001, 002, 011 |
| 030 | knowledge_chunks | 029 |
| 031 | agents | 001, 002 |
| 032 | agent_capabilities | 031, 007 |
| 033 | tools | 001 |
| 034 | tool_capabilities | 033, 007 |
| 035 | agent_runs | 031, 002 |
| 036 | tool_runs | 035, 033 |
| 037 | agent_tasks | 025, 031, 011 |
| 038 | agent_permissions | 031, 007, 011 |
| 039 | agent_messages | 031, 002 |
| 040 | automations | 001, 002 |
| 041 | automation_triggers | 040 |
| 042 | automation_actions | 040, 033 |
| 043 | anomalies | 001, 002, 011, 017, 022 |
| 044 | anomaly_evidence | 043 |
| 045 | audit_logs | các bảng cần trace, tạo cuối cùng |

## 4. DDL rules
- Core PK dùng UUID/UUIDv7.
- Target tenant tables cần UNIQUE(id, organization_id).
- organization_members cần UNIQUE(organization_id, user_id).
- Composite FK locked trong MIGRATION_CONTRACT_V2.md phải được tạo cùng child migration.
- RESTRICT cho history/auth/credential/audit/run trace.
- CASCADE chỉ cho mapping thuần quan hệ đã được contract cho phép.
- FK lookup phải có index; tenant index ưu tiên organization_id.
- CHECK lấy trực tiếp từ DATABASE_V2_DETAILED.md.

## 5. Verification
Identity/Auth: 001 → 010.
Resource/Package/Device: 011 → 020.
Activity/Task: 021 → 025.
Conversation/Knowledge: 026 → 030.
Agent/Tool/Run/A2A: 031 → 039.
Automation/Anomaly/Audit: 040 → 045.

## 6. Acceptance checklist
- [ ] 45/45 migration unit.
- [ ] Không có dependency cycle.
- [ ] FK target tồn tại trước child.
- [ ] Composite tenant FK đầy đủ.
- [ ] Composite UNIQUE đầy đủ.
- [ ] ON DELETE đúng contract.
- [ ] UNIQUE/CHECK/INDEX đúng contract.
- [ ] Cross-organization reference bị database từ chối.
- [x] PostgreSQL clean migration pass cho 001 → 010.
- [x] Acceptance test AT-001 → AT-008 pass cho 001 → 010.
- [ ] Schema diff = 0 ngoài thay đổi đã khóa.

## 7. Quy trình tiếp theo
1. Review và khóa tài liệu này.
2. SQL migration 001 → 010 đã triển khai và verify PASS.
3. Thiết kế/triển khai SQL migration 011 → 020.
4. Chạy 011 → 020 trên PostgreSQL sạch hoặc database reset từ đầu theo gate tương ứng.
5. Chạy acceptance tests 011 → 020.
6. Sau khi pass mới mở rộng sang 021 → 030.

---

# Migration Review Lock — 2026-09-21 09:35 +07:00

Thiết kế 001→045 đủ điều kiện chuyển sang production SQL sau khi áp dụng các lock: Agent tenant scope, Task schema, Evidence source FKs và Automation tenant scope.


---

# Verification Update — 2026-09-21 08:30:00 +07:00

- Migration 001 → 010: **PASS trên PostgreSQL 18.6**.
- Acceptance AT-001 → AT-008: **PASS**.
- Database sạch trước migration; acceptance test dùng transaction và **ROLLBACK**.
- Gate 001 → 010 đã đóng.

## Verification Gate — Migration 011 → 020

- PostgreSQL 18.6 thực tế đã chạy Migration 011 → 020 thành công.
- Acceptance AT-011 → AT-022 đạt **12/12 PASS**.
- Acceptance transaction kết thúc bằng ROLLBACK.
- Gate 011 → 020 được đóng.
- Migration 021 → 030 là gate tiếp theo.


## Verification Gate — Migration 021 → 030

- Production SQL 021→030: **CREATED**.
- Acceptance AT-021→AT-030: **CREATED**.
- Chưa chạy database thực tế ở bước này.
- Gate 021→030: **OPEN / awaiting PostgreSQL verification**.
