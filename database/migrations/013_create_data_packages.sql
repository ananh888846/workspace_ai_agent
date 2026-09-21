BEGIN;

CREATE TABLE data_packages (
  id UUID PRIMARY KEY DEFAULT uuidv7(),
  organization_id UUID NOT NULL,
  owner_user_id UUID NOT NULL,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  package_type VARCHAR(64) NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_data_packages_id_org UNIQUE (id, organization_id),
  CONSTRAINT fk_data_packages_org
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE RESTRICT,
  CONSTRAINT fk_data_packages_owner_member
    FOREIGN KEY (organization_id, owner_user_id)
    REFERENCES organization_members(organization_id, user_id) ON DELETE RESTRICT
);

CREATE INDEX idx_data_packages_org ON data_packages(organization_id);
CREATE INDEX idx_data_packages_owner ON data_packages(owner_user_id);
CREATE INDEX idx_data_packages_type ON data_packages(package_type);
CREATE INDEX idx_data_packages_status ON data_packages(status);
CREATE INDEX idx_data_packages_created_at ON data_packages(created_at);

COMMIT;
