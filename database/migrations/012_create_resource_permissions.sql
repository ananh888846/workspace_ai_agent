BEGIN;

CREATE TABLE resource_permissions (
  id UUID PRIMARY KEY DEFAULT uuidv7(),
  organization_id UUID NOT NULL,
  resource_id UUID NOT NULL,
  user_id UUID NOT NULL,
  action VARCHAR(100) NOT NULL,
  effect VARCHAR(16) NOT NULL DEFAULT 'allow',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ,
  CONSTRAINT uq_resource_permissions_resource_user_action
    UNIQUE (resource_id, user_id, action),
  CONSTRAINT fk_resource_permissions_org
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE RESTRICT,
  CONSTRAINT fk_resource_permissions_resource_same_org
    FOREIGN KEY (resource_id, organization_id)
    REFERENCES resources(id, organization_id) ON DELETE RESTRICT,
  CONSTRAINT fk_resource_permissions_user_member
    FOREIGN KEY (organization_id, user_id)
    REFERENCES organization_members(organization_id, user_id) ON DELETE RESTRICT,
  CONSTRAINT ck_resource_permissions_expiry
    CHECK (expires_at IS NULL OR expires_at >= created_at)
);

CREATE INDEX idx_resource_permissions_org ON resource_permissions(organization_id);
CREATE INDEX idx_resource_permissions_resource ON resource_permissions(resource_id);
CREATE INDEX idx_resource_permissions_user ON resource_permissions(user_id);
CREATE INDEX idx_resource_permissions_expires ON resource_permissions(expires_at);

COMMIT;
