# Acceptance Test — Migration 001 → 010

> **Verification status (2026-09-21): PASS.** Migration 001 → 010 đã chạy trên PostgreSQL 18.6 sạch và AT-001 → AT-008 đều PASS. Test transaction kết thúc bằng ROLLBACK.

## Mục tiêu

Kiểm tra clean PostgreSQL cho Migration 001 → 010 theo contract V2.1.

Suite xác nhận:
- UUIDv7 native của PostgreSQL 18+.
- FK và composite tenant FK.
- Account Grant không thể vượt tenant boundary.
- Account phải thuộc đúng owner.
- Temporal CHECK.
- Role/Permission mapping và FK.
- Test data được rollback sau khi chạy.

## Trạng thái verification

- PostgreSQL: 18.6
- Database: clean trước migration
- Migration 001 → 010: PASS
- AT-001 → AT-008: PASS
- Test data: ROLLBACK
- Gate tiếp theo: review và triển khai Migration 011 → 020.

## Cách chạy

Từ database sạch:

```bash
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f database/migrations/001_create_organizations.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f database/migrations/002_create_users.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f database/migrations/003_create_organization_members.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f database/migrations/004_create_user_accounts.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f database/migrations/005_create_account_credentials.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f database/migrations/006_create_roles.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f database/migrations/007_create_permissions.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f database/migrations/008_create_user_roles.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f database/migrations/009_create_role_permissions.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f database/migrations/010_create_account_grants.sql

psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f database/tests/acceptance_001_010.sql
```

## Kết quả đạt

Kết quả cuối phải có:

```
AT-001 PASS
AT-002 PASS
AT-003 PASS
AT-004 PASS
AT-005 PASS
AT-006 PASS
AT-007 PASS
AT-008 PASS
```

Nếu một test thất bại, **không tiếp tục 011 → 020**. Sửa migration/contract trước, chạy lại từ database sạch.

> Lưu ý: suite này mới là acceptance SQL. Chưa được coi là "đã pass" cho tới khi thực sự chạy trên PostgreSQL 18+ sạch.
