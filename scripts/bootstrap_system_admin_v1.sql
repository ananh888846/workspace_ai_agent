-- Bootstrap System Administrator V1.
-- Chạy bằng psql sau khi Migration 001 -> 051 đã hoàn tất.
-- Không lưu mật khẩu Web/Laravel hoặc credential provider trong file này.

\set ON_ERROR_STOP on

\if :{?ADMIN_NAME}
\else
  \echo 'ADMIN_NAME is required'
  \quit 1
\endif
\if :{?ADMIN_EMAIL}
\else
  \echo 'ADMIN_EMAIL is required'
  \quit 1
\endif
\if :{?ADMIN_ORG_NAME}
\else
  \echo 'ADMIN_ORG_NAME is required'
  \quit 1
\endif

BEGIN;

WITH existing AS (
  SELECT id FROM organizations
  WHERE name = :'ADMIN_ORG_NAME' AND organization_type = 'system'
  ORDER BY created_at LIMIT 1
),
created AS (
  INSERT INTO organizations (name, organization_type, status)
  SELECT :'ADMIN_ORG_NAME', 'system', 'active'
  WHERE NOT EXISTS (SELECT 1 FROM existing)
  RETURNING id
)
SELECT id FROM created
UNION ALL SELECT id FROM existing
LIMIT 1
\gset admin_org_

WITH existing AS (
  SELECT id FROM users WHERE email = :'ADMIN_EMAIL' LIMIT 1
),
created AS (
  INSERT INTO users (name, email, status)
  SELECT :'ADMIN_NAME', :'ADMIN_EMAIL', 'active'
  WHERE NOT EXISTS (SELECT 1 FROM existing)
  RETURNING id
)
SELECT id FROM created
UNION ALL SELECT id FROM existing
LIMIT 1
\gset admin_user_

INSERT INTO organization_members (organization_id, user_id, member_role, status)
VALUES (:'admin_org_id', :'admin_user_id', 'owner', 'active')
ON CONFLICT (organization_id, user_id)
DO UPDATE SET member_role = 'owner', status = 'active';

INSERT INTO roles (name, description)
VALUES ('system_admin', 'Quản trị hệ thống theo toàn bộ Permission catalog hiện có.')
ON CONFLICT (name)
DO UPDATE SET description = EXCLUDED.description, updated_at = now();

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r CROSS JOIN permissions p
WHERE r.name = 'system_admin'
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO user_roles (user_id, role_id)
SELECT :'admin_user_id', r.id
FROM roles r
WHERE r.name = 'system_admin'
ON CONFLICT (user_id, role_id) DO NOTHING;

COMMIT;

SELECT
  :'admin_user_id'::uuid AS admin_user_id,
  :'admin_org_id'::uuid AS admin_organization_id,
  (SELECT id FROM roles WHERE name = 'system_admin') AS system_admin_role_id,
  (SELECT count(*)
   FROM role_permissions rp
   JOIN roles r ON r.id = rp.role_id
   WHERE r.name = 'system_admin') AS system_admin_permission_count;
