BEGIN;

CREATE TABLE account_grants (
  id UUID PRIMARY KEY,
  organization_id UUID NOT NULL,
  owner_user_id UUID NOT NULL,
  grantee_user_id UUID NOT NULL,
  user_account_id UUID NOT NULL,
  scope JSONB NOT NULL DEFAULT '{}'::jsonb,
  status VARCHAR(32) NOT NULL DEFAULT 'active',
  starts_at TIMESTAMPTZ,
  expires_at TIMESTAMPTZ,
  revoked_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_account_grants_id_org UNIQUE (id, organization_id),
  CONSTRAINT fk_account_grants_org FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE RESTRICT,
  CONSTRAINT fk_account_grants_owner_member FOREIGN KEY (organization_id, owner_user_id) REFERENCES organization_members(organization_id, user_id) ON DELETE RESTRICT,
  CONSTRAINT fk_account_grants_grantee_member FOREIGN KEY (organization_id, grantee_user_id) REFERENCES organization_members(organization_id, user_id) ON DELETE RESTRICT,
  CONSTRAINT fk_account_grants_account_owner FOREIGN KEY (user_account_id, owner_user_id) REFERENCES user_accounts(id, user_id) ON DELETE RESTRICT,
  CONSTRAINT ck_account_grants_expiry CHECK (expires_at IS NULL OR starts_at IS NULL OR expires_at >= starts_at)
);
CREATE INDEX idx_account_grants_org ON account_grants(organization_id);
CREATE INDEX idx_account_grants_owner ON account_grants(owner_user_id);
CREATE INDEX idx_account_grants_grantee ON account_grants(grantee_user_id);
CREATE INDEX idx_account_grants_account ON account_grants(user_account_id);
CREATE INDEX idx_account_grants_status ON account_grants(status);
CREATE INDEX idx_account_grants_expires ON account_grants(expires_at);
COMMIT;
