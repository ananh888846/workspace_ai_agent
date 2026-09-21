BEGIN;

CREATE TABLE organizations (
  id UUID PRIMARY KEY DEFAULT uuidv7(),
  name VARCHAR(255) NOT NULL,
  organization_type VARCHAR(64) NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'active',
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_organizations_type ON organizations(organization_type);
CREATE INDEX idx_organizations_status ON organizations(status);
CREATE INDEX idx_organizations_created_at ON organizations(created_at);
COMMIT;
