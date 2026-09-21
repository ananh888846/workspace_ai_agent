-- Google Calendar V1 local PostgreSQL test fixture.
-- Run only after migrations 001-051 are applied to PostgreSQL.
-- This fixture creates tenant/authorization/account METADATA only.
-- It never creates OAuth credentials and never stores access/refresh tokens.
--
-- IMPORTANT:
-- - The Google account row is intentionally pending OAuth.
-- - Do not mark it active until a real OAuth credential has been stored through
--   the CredentialResolver/OAuth flow.
-- - Do not replace placeholders with OAuth tokens in this file.

BEGIN;

-- 1. Local tenant.
INSERT INTO organizations (id, name, organization_type, status)
SELECT uuidv7(), 'Local Calendar Test', 'personal', 'active'
WHERE NOT EXISTS (
    SELECT 1
    FROM organizations
    WHERE name = 'Local Calendar Test'
);

-- 2. Local test user + tenant membership.
WITH org AS (
    SELECT id
    FROM organizations
    WHERE name = 'Local Calendar Test'
    ORDER BY created_at DESC
    LIMIT 1
),
usr AS (
    INSERT INTO users (id, name, email, status)
    SELECT uuidv7(), 'Calendar Test User',
           'calendar-test@local.invalid', 'active'
    WHERE NOT EXISTS (
        SELECT 1
        FROM users
        WHERE email = 'calendar-test@local.invalid'
    )
    RETURNING id
)
INSERT INTO organization_members (
    organization_id,
    user_id,
    member_role,
    status
)
SELECT
    org.id,
    COALESCE(
        usr.id,
        (SELECT id FROM users WHERE email = 'calendar-test@local.invalid')
    ),
    'owner',
    'active'
FROM org
LEFT JOIN usr ON TRUE
ON CONFLICT (organization_id, user_id) DO NOTHING;

-- 3. Calendar capabilities used by the local authorization fixture.
INSERT INTO permissions (id, resource, action, description)
VALUES
    (uuidv7(), 'calendar', 'read', 'Read Google Calendar events'),
    (uuidv7(), 'calendar', 'write', 'Create/update/delete Google Calendar events')
ON CONFLICT (resource, action) DO NOTHING;

INSERT INTO roles (id, name, description)
VALUES (
    uuidv7(),
    'calendar_test',
    'Local Google Calendar V1 test role'
)
ON CONFLICT (name) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p
  ON p.resource = 'calendar'
 AND p.action IN ('read', 'write')
WHERE r.name = 'calendar_test'
ON CONFLICT (role_id, permission_id) DO NOTHING;

INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM users u
JOIN roles r ON r.name = 'calendar_test'
WHERE u.email = 'calendar-test@local.invalid'
ON CONFLICT (user_id, role_id) DO NOTHING;

-- 4. Google account metadata.
-- The account is pending OAuth because no real credential exists yet.
-- external_account_id is deliberately a local placeholder.
INSERT INTO user_accounts (
    id,
    user_id,
    provider,
    account_type,
    external_account_id,
    display_name,
    email,
    status,
    metadata
)
SELECT
    uuidv7(),
    u.id,
    'google',
    'google_calendar',
    'local-calendar-oauth-pending',
    'Local Calendar Google Account',
    NULL,
    'pending_oauth',
    jsonb_build_object(
        'fixture', true,
        'oauth_status', 'pending',
        'note', 'Replace with a real Google account through the OAuth flow'
    )
FROM users u
WHERE u.email = 'calendar-test@local.invalid'
  AND NOT EXISTS (
      SELECT 1
      FROM user_accounts ua
      WHERE ua.user_id = u.id
        AND ua.provider = 'google'
        AND ua.external_account_id = 'local-calendar-oauth-pending'
  );

-- 5. No resource is created here.
-- Calendar resources should be created only after the real Google account
-- has been connected and the provider resource has been discovered.
-- No account_credentials row is created by this fixture.

COMMIT;

-- Verification output.
SELECT
    u.id AS user_id,
    u.email,
    u.status AS user_status,
    o.id AS organization_id,
    o.name AS organization_name,
    om.member_role,
    om.status AS membership_status
FROM users u
JOIN organization_members om ON om.user_id = u.id
JOIN organizations o ON o.id = om.organization_id
WHERE u.email = 'calendar-test@local.invalid';

SELECT
    ua.id,
    ua.user_id,
    ua.provider,
    ua.account_type,
    ua.external_account_id,
    ua.email,
    ua.status,
    ua.metadata
FROM user_accounts ua
JOIN users u ON u.id = ua.user_id
WHERE u.email = 'calendar-test@local.invalid';

SELECT
    r.name AS role_name,
    p.resource,
    p.action
FROM user_roles ur
JOIN roles r ON r.id = ur.role_id
JOIN role_permissions rp ON rp.role_id = r.id
JOIN permissions p ON p.id = rp.permission_id
JOIN users u ON u.id = ur.user_id
WHERE u.email = 'calendar-test@local.invalid'
ORDER BY p.resource, p.action;
