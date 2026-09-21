CREATE TABLE automations (
  id UUID PRIMARY KEY DEFAULT uuidv7(),
  organization_id UUID NOT NULL,
  owner_user_id UUID NOT NULL,
  name VARCHAR(255) NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_automations_id_org UNIQUE (id, organization_id),
  CONSTRAINT uq_automations_org_name UNIQUE (organization_id, name),
  FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE RESTRICT,
  FOREIGN KEY (organization_id, owner_user_id)
    REFERENCES organization_members(organization_id, user_id) ON DELETE RESTRICT
);

CREATE INDEX idx_automations_org_status_updated
  ON automations (organization_id, status, updated_at);
CREATE INDEX idx_automations_owner_created
  ON automations (owner_user_id, created_at);
