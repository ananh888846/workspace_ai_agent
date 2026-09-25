-- Acceptance: System Administrator V1.
-- Chạy sau Migration 001 -> 051. Toàn bộ fixture được ROLLBACK.

BEGIN;

DO $$
DECLARE
  v_org_id UUID := uuidv7();
  v_user_id UUID := uuidv7();
  v_role_id UUID := uuidv7();
  v_permission_a UUID := uuidv7();
  v_permission_b UUID := uuidv7();
  v_permission_count INTEGER;
  v_mapped_count INTEGER;
BEGIN
  INSERT INTO organizations(id, name, organization_type, status)
  VALUES (v_org_id, 'AT System Admin Org', 'system', 'active');

  INSERT INTO users(id, name, email, status)
  VALUES (
    v_user_id,
    'AT System Administrator',
    'at-system-admin-' || replace(v_org_id::text, '-', '') || '@example.invalid',
    'active'
  );

  INSERT INTO organization_members(organization_id, user_id, member_role, status)
  VALUES (v_org_id, v_user_id, 'owner', 'active');

  INSERT INTO roles(id, name, description)
  VALUES (v_role_id, 'system_admin', 'AT system administrator role');

  INSERT INTO permissions(id, resource, action, description)
  VALUES
    (v_permission_a, 'at_system_admin_test', 'read', 'AT permission A'),
    (v_permission_b, 'at_system_admin_test', 'write', 'AT permission B');

  -- system_admin phải được map toàn bộ Permission catalog hiện tại,
  -- không chỉ các Permission fixture của acceptance test.
  INSERT INTO role_permissions(role_id, permission_id)
  SELECT v_role_id, id
  FROM permissions;

  INSERT INTO user_roles(user_id, role_id)
  VALUES (v_user_id, v_role_id);

  SELECT count(*) INTO v_permission_count FROM permissions;

  SELECT count(*) INTO v_mapped_count
  FROM role_permissions rp
  WHERE rp.role_id = v_role_id;

  IF v_mapped_count <> v_permission_count THEN
    RAISE EXCEPTION
      'AT-SYSADMIN-04 FAIL: system_admin mapped %, catalog has %',
      v_mapped_count, v_permission_count;
  END IF;

  IF EXISTS (
    SELECT 1 FROM permissions
    WHERE resource = '*' OR action = '*'
  ) THEN
    RAISE EXCEPTION 'AT-SYSADMIN-05 FAIL: wildcard permission detected';
  END IF;

  DELETE FROM organization_members
  WHERE organization_id = v_org_id AND user_id = v_user_id;

  IF EXISTS (
    SELECT 1 FROM organization_members
    WHERE organization_id = v_org_id AND user_id = v_user_id
  ) THEN
    RAISE EXCEPTION 'AT-SYSADMIN-06 FAIL: membership deletion did not apply';
  END IF;

  IF v_permission_count <> 3 THEN
    RAISE EXCEPTION
      'AT-SYSADMIN-07 FAIL: canonical catalog expected 3 permissions, found %',
      v_permission_count;
  END IF;

  RAISE NOTICE 'AT-SYSADMIN-01..07 PASS';
END $$;

ROLLBACK;
