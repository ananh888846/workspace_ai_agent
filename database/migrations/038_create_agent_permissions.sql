CREATE TABLE agent_permissions (
  id UUID PRIMARY KEY DEFAULT uuidv7(),
  organization_id UUID NOT NULL,
  grantor_agent_id UUID NOT NULL,
  grantee_agent_id UUID NOT NULL,
  capability VARCHAR(100) NOT NULL,
  action VARCHAR(100) NOT NULL,
  resource_id UUID,
  effect VARCHAR(16) NOT NULL DEFAULT 'allow',
  starts_at TIMESTAMPTZ,
  expires_at TIMESTAMPTZ,
  revoked_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_agent_permissions_scope
    UNIQUE NULLS NOT DISTINCT
    (grantor_agent_id, grantee_agent_id, capability, action, resource_id),
  CONSTRAINT ck_agent_permissions_expiry
    CHECK (expires_at IS NULL OR starts_at IS NULL OR expires_at >= starts_at),
  FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE RESTRICT,
  FOREIGN KEY (grantor_agent_id, organization_id)
    REFERENCES agents(id, organization_id) ON DELETE RESTRICT,
  FOREIGN KEY (grantee_agent_id, organization_id)
    REFERENCES agents(id, organization_id) ON DELETE RESTRICT,
  FOREIGN KEY (resource_id, organization_id)
    REFERENCES resources(id, organization_id) ON DELETE RESTRICT
);

CREATE INDEX idx_agent_permissions_org ON agent_permissions (organization_id);
CREATE INDEX idx_agent_permissions_grantee_capability_action
  ON agent_permissions (grantee_agent_id, capability, action);
CREATE INDEX idx_agent_permissions_expires_at
  ON agent_permissions (expires_at)
  WHERE expires_at IS NOT NULL;
