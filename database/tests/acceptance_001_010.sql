-- Acceptance Suite: Migration 001 -> 010
-- PostgreSQL 18+
-- Prerequisite: run database/migrations/001_create_organizations.sql through
--               database/migrations/010_create_account_grants.sql first.
-- This suite is transactional and rolls back all test data at the end.

BEGIN;

DO $$
BEGIN
  IF current_setting('server_version_num')::int < 180000 THEN
    RAISE EXCEPTION 'AT-000 FAILED: PostgreSQL 18+ is required for native uuidv7()';
  END IF;
END $$;

-- Base fixtures
INSERT INTO organizations (id, name, organization_type)
VALUES
  ('00000000-0000-0000-0000-000000000001', 'AT Org A', 'personal'),
  ('00000000-0000-0000-0000-000000000002', 'AT Org B', 'personal');

INSERT INTO users (id, name, email)
VALUES
  ('00000000-0000-0000-0000-000000000011', 'AT User A', 'at-user-a@example.test'),
  ('00000000-0000-0000-0000-000000000012', 'AT User B', 'at-user-b@example.test'),
  ('00000000-0000-0000-0000-000000000013', 'AT User C', 'at-user-c@example.test');

INSERT INTO organization_members (organization_id, user_id)
VALUES
  ('00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000011'),
  ('00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000012'),
  ('00000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000013');

INSERT INTO user_accounts (
  id, user_id, provider, account_type, external_account_id, display_name, email
)
VALUES (
  '00000000-0000-0000-0000-000000000021',
  '00000000-0000-0000-0000-000000000011',
  'google',
  'gmail',
  'at-google-account-a',
  'AT Gmail A',
  'at-user-a@gmail.com'
);

INSERT INTO roles (id, name) VALUES
  ('00000000-0000-0000-0000-000000000031', 'at_role');

INSERT INTO permissions (id, resource, action) VALUES
  ('00000000-0000-0000-0000-000000000041', 'drive', 'read');

-- AT-001: owner belongs to Org A but grant says Org B -> REJECT
DO $$
BEGIN
  BEGIN
    INSERT INTO account_grants (
      organization_id, owner_user_id, grantee_user_id, user_account_id, scope
    ) VALUES (
      '00000000-0000-0000-0000-000000000002',
      '00000000-0000-0000-0000-000000000011',
      '00000000-0000-0000-0000-000000000013',
      '00000000-0000-0000-0000-000000000021',
      '{}'
    );
    RAISE EXCEPTION 'AT-001 FAILED: cross-tenant owner was accepted';
  EXCEPTION WHEN foreign_key_violation THEN
    NULL;
  END;
END $$;

-- AT-002: grantee is not a member of the grant organization -> REJECT
DO $$
BEGIN
  BEGIN
    INSERT INTO account_grants (
      organization_id, owner_user_id, grantee_user_id, user_account_id, scope
    ) VALUES (
      '00000000-0000-0000-0000-000000000001',
      '00000000-0000-0000-0000-000000000011',
      '00000000-0000-0000-0000-000000000013',
      '00000000-0000-0000-0000-000000000021',
      '{}'
    );
    RAISE EXCEPTION 'AT-002 FAILED: cross-tenant grantee was accepted';
  EXCEPTION WHEN foreign_key_violation THEN
    NULL;
  END;
END $$;

-- AT-003: account belongs to User A but owner_user_id is User B -> REJECT
DO $$
BEGIN
  BEGIN
    INSERT INTO account_grants (
      organization_id, owner_user_id, grantee_user_id, user_account_id, scope
    ) VALUES (
      '00000000-0000-0000-0000-000000000001',
      '00000000-0000-0000-0000-000000000012',
      '00000000-0000-0000-0000-000000000011',
      '00000000-0000-0000-0000-000000000021',
      '{}'
    );
    RAISE EXCEPTION 'AT-003 FAILED: account owner mismatch was accepted';
  EXCEPTION WHEN foreign_key_violation THEN
    NULL;
  END;
END $$;

-- AT-004: same organization, correct owner, correct account -> ACCEPT
INSERT INTO account_grants (
  organization_id, owner_user_id, grantee_user_id, user_account_id, scope
) VALUES (
  '00000000-0000-0000-0000-000000000001',
  '00000000-0000-0000-0000-000000000011',
  '00000000-0000-0000-0000-000000000012',
  '00000000-0000-0000-0000-000000000021',
  '{"drive":["read"]}'
);

-- AT-005: expires_at < starts_at -> REJECT
DO $$
BEGIN
  BEGIN
    INSERT INTO account_grants (
      organization_id, owner_user_id, grantee_user_id, user_account_id,
      starts_at, expires_at, scope
    ) VALUES (
      '00000000-0000-0000-0000-000000000001',
      '00000000-0000-0000-0000-000000000011',
      '00000000-0000-0000-0000-000000000012',
      '00000000-0000-0000-0000-000000000021',
      '2026-09-21 10:00:00+00',
      '2026-09-21 09:00:00+00',
      '{}'
    );
    RAISE EXCEPTION 'AT-005 FAILED: invalid time range was accepted';
  EXCEPTION WHEN check_violation THEN
    NULL;
  END;
END $$;

-- AT-006: role/permission mapping succeeds
INSERT INTO user_roles (user_id, role_id)
VALUES (
  '00000000-0000-0000-0000-000000000011',
  '00000000-0000-0000-0000-000000000031'
);

INSERT INTO role_permissions (role_id, permission_id)
VALUES (
  '00000000-0000-0000-0000-000000000031',
  '00000000-0000-0000-0000-000000000041'
);

-- AT-007: role does not exist -> FK REJECT
DO $$
BEGIN
  BEGIN
    INSERT INTO user_roles (user_id, role_id)
    VALUES (
      '00000000-0000-0000-0000-000000000011',
      '00000000-0000-0000-0000-000000000099'
    );
    RAISE EXCEPTION 'AT-007 FAILED: missing role was accepted';
  EXCEPTION WHEN foreign_key_violation THEN
    NULL;
  END;
END $$;

-- AT-008: permission does not exist -> FK REJECT
DO $$
BEGIN
  BEGIN
    INSERT INTO role_permissions (role_id, permission_id)
    VALUES (
      '00000000-0000-0000-0000-000000000031',
      '00000000-0000-0000-0000-000000000099'
    );
    RAISE EXCEPTION 'AT-008 FAILED: missing permission was accepted';
  EXCEPTION WHEN foreign_key_violation THEN
    NULL;
  END;
END $$;

-- Explicit success assertions.
DO $$
DECLARE
  grant_count integer;
  mapping_count integer;
BEGIN
  SELECT count(*) INTO grant_count
  FROM account_grants
  WHERE organization_id = '00000000-0000-0000-0000-000000000001'
    AND owner_user_id = '00000000-0000-0000-0000-000000000011'
    AND grantee_user_id = '00000000-0000-0000-0000-000000000012';

  IF grant_count <> 1 THEN
    RAISE EXCEPTION 'AT-004 FAILED: expected one valid account grant, got %', grant_count;
  END IF;

  SELECT count(*) INTO mapping_count
  FROM role_permissions
  WHERE role_id = '00000000-0000-0000-0000-000000000031'
    AND permission_id = '00000000-0000-0000-0000-000000000041';

  IF mapping_count <> 1 THEN
    RAISE EXCEPTION 'AT-006 FAILED: expected one role-permission mapping, got %', mapping_count;
  END IF;
END $$;

ROLLBACK;

SELECT 'AT-001 PASS' AS result
UNION ALL SELECT 'AT-002 PASS'
UNION ALL SELECT 'AT-003 PASS'
UNION ALL SELECT 'AT-004 PASS'
UNION ALL SELECT 'AT-005 PASS'
UNION ALL SELECT 'AT-006 PASS'
UNION ALL SELECT 'AT-007 PASS'
UNION ALL SELECT 'AT-008 PASS';
