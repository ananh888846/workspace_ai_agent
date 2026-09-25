BEGIN;

-- Canonical application Permission catalog V1.
-- Source of truth: workspace-ai-agent-ecosystem/ARCHITECTURE/PERMISSION_CATALOG_V1.md
-- Idempotent by the existing UNIQUE(resource, action) constraint.
-- Provider OAuth scopes and resource/agent permission layers are intentionally excluded.

INSERT INTO permissions (resource, action, description)
VALUES
  ('calendar', 'read', 'Read Calendar data, including scheduling/free-busy reads.'),
  ('calendar', 'write', 'Create, update, and delete Calendar events.'),
  ('knowledge', 'read', 'Read/ingest Knowledge sources, including approved Threads → Knowledge ingestion.')
ON CONFLICT (resource, action) DO UPDATE
SET description = EXCLUDED.description;

COMMIT;
