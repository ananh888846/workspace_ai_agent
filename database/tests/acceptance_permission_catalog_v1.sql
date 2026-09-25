-- Acceptance: canonical Permission Catalog V1.
-- Chạy sau Migration 052. Fixture changes are rolled back.

BEGIN;

DO $$
DECLARE
  v_count INTEGER;
  v_wildcards INTEGER;
  v_expected INTEGER := 3;
  v_missing INTEGER;
  v_extra INTEGER;
BEGIN
  SELECT count(*) INTO v_count FROM permissions;

  IF v_count <> v_expected THEN
    RAISE EXCEPTION 'AT-PERM-01 FAIL: expected %, found % permissions', v_expected, v_count;
  END IF;

  SELECT count(*) INTO v_missing
  FROM (
    VALUES
      ('calendar', 'read'),
      ('calendar', 'write'),
      ('knowledge', 'read')
  ) AS expected(resource, action)
  WHERE NOT EXISTS (
    SELECT 1
    FROM permissions p
    WHERE p.resource = expected.resource
      AND p.action = expected.action
  );

  IF v_missing <> 0 THEN
    RAISE EXCEPTION 'AT-PERM-02 FAIL: % canonical permissions missing', v_missing;
  END IF;

  SELECT count(*) INTO v_extra
  FROM permissions p
  WHERE NOT (
    (p.resource = 'calendar' AND p.action = 'read')
    OR (p.resource = 'calendar' AND p.action = 'write')
    OR (p.resource = 'knowledge' AND p.action = 'read')
  );

  IF v_extra <> 0 THEN
    RAISE EXCEPTION 'AT-PERM-03 FAIL: % unexpected permissions found', v_extra;
  END IF;

  SELECT count(*) INTO v_wildcards
  FROM permissions
  WHERE resource = '*' OR action = '*';

  IF v_wildcards <> 0 THEN
    RAISE EXCEPTION 'AT-PERM-04 FAIL: wildcard permission detected';
  END IF;

  RAISE NOTICE 'AT-PERM-01..04 PASS';
END $$;

ROLLBACK;
