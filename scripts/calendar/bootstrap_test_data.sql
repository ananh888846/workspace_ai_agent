-- Calendar V1 local test data bootstrap.
-- Run only after migrations 001-051 are applied to PostgreSQL.
-- This file creates metadata/authorization fixtures only.
-- NEVER put OAuth access/refresh tokens in this file.

BEGIN;

-- 1. Tenant + user
INSERT INTO organizations (id, name, organization_type, status)
VALUES (
    uuidv7(),
    'Local Calendar Test',
    'personal',
    'active'
)
ON CONFLICT DO NOTHING;

-- Reuse by name so the script can be inspected safely before execution.
-- The following CTEs keep all IDs inside one transaction.
WITH org AS (
    SELECT id FROM organizations
    WHERE name = 'Local Calendar Test'
    ORDER BY created_at DESC
    LIMIT 1
),
new_user AS (
    INSERT INTO users (id, name, email, status)
    SELECT uuidv7(), 'Calendar Test User',
           'calendar-test@local.invalid', 'active'
    WHERE NOT EXISTS (
        SELECT 1 FROM users WHERE email = 'calendar-test@local.invalid'
    )
    RETURNING id
)
INSERT INTO organization_members (organization_id, user_id, member_role, status)
SELECT org.id, COALESCE(new_user.id,
                       (SELECT id FROM users WHERE email='calendar-test@local.invalid')),
       'owner', 'active'
FROM org
LEFT JOIN new_user ON TRUE
ON CONFLICT DO NOTHING;

-- 2. Capability permissions
INSERT INTO permissions (id, resource, action, description)
VALUES
  (uuidv7(), 'calendar', 'read', 'Read Google Calendar events'),
  (uuidv7(), 'calendar', 'write', 'Create/update/delete Google Calendar events')
ON CONFLICT (resource, action) DO NOTHING;

-- Create a dedicated local test role.
INSERT INTO roles (id, name, description)
VALUES (uuidv7(), 'calendar_test', 'Local Google Calendar V1 test role')
ON CONFLICT (name) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p
  ON p.resource='calendar'
 AND p.action IN ('read','write')
WHERE r.name='calendar_test'
ON CONFLICT DO NOTHING;

INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM users u
JOIN roles r ON r.name='calendar_test'
WHERE u.email='calendar-test@local.invalid'
ON CONFLICT DO NOTHING;

-- 3. Google external account metadata.
-- external_account_id must be the actual Google account identifier/email
-- used by the OAuth connection.
INSERT INTO user_accounts (
    id, user_id, provider, account_type, external_account_id,
    display_name, email, status, metadata
)
SELECT
    uuidv7(), u.id, 'google', 'google_calendar',
    'REPLACE_WITH_REAL_GOOGLE_ACCOUNT_ID',
    'Local Calendar Google Account',
    'REPLACE_WITH_REAL_GOOGLE_EMAIL',
    'active', '{}'::jsonb
FROM users u
WHERE u.email='calendar-test@local.invalid'
  AND NOT EXISTS (
      SELECT 1 FROM user_accounts ua
      WHERE ua.user_id=u.id
        AND ua.provider='google'
        AND ua.external_account_id='REPLACE_WITH_REAL_GOOGLE_ACCOUNT_ID'
  );

-- 4. Calendar resource metadata.
-- Replace the account/resource IDs after OAuth account creation.
-- We intentionally do not create fake provider credentials.
COMMIT;

SELECT
    u.id AS user_id,
    u.email,
    o.id AS organization_id,
    o.name AS organization_name
FROM users u
JOIN organization_members om ON om.user_id=u.id
JOIN organizations o ON o.id=om.organization_id
WHERE u.email='calendar-test@local.invalid';

SELECT
    id, provider, account_type, external_account_id, email, status
FROM user_accounts
WHERE user_id = (
    SELECT id FROM users WHERE email='calendar-test@local.invalid'
);
