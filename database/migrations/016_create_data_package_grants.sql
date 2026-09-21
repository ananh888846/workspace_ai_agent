BEGIN;

CREATE TABLE data_package_grants (
  id UUID PRIMARY KEY DEFAULT uuidv7(),
  organization_id UUID NOT NULL,
  package_version_id UUID NOT NULL,
  user_id UUID NOT NULL,
  permission VARCHAR(100) NOT NULL,
  starts_at TIMESTAMPTZ,
  expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  revoked_at TIMESTAMPTZ,
  CONSTRAINT uq_data_package_grants_version_user_permission
    UNIQUE (package_version_id, user_id, permission),
  CONSTRAINT uq_data_package_grants_id_org
    UNIQUE (id, organization_id),
  CONSTRAINT fk_data_package_grants_org
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE RESTRICT,
  CONSTRAINT fk_data_package_grants_version_same_org
    FOREIGN KEY (package_version_id, organization_id)
    REFERENCES data_package_versions(id, organization_id) ON DELETE RESTRICT,
  CONSTRAINT fk_data_package_grants_user_member
    FOREIGN KEY (organization_id, user_id)
    REFERENCES organization_members(organization_id, user_id) ON DELETE RESTRICT,
  CONSTRAINT ck_data_package_grants_expiry
    CHECK (expires_at IS NULL OR starts_at IS NULL OR expires_at >= starts_at)
);

CREATE INDEX idx_data_package_grants_org ON data_package_grants(organization_id);
CREATE INDEX idx_data_package_grants_version ON data_package_grants(package_version_id);
CREATE INDEX idx_data_package_grants_user ON data_package_grants(user_id);
CREATE INDEX idx_data_package_grants_expires ON data_package_grants(expires_at);

COMMIT;
