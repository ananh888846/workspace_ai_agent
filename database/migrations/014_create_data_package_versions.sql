BEGIN;

CREATE TABLE data_package_versions (
  id UUID PRIMARY KEY DEFAULT uuidv7(),
  organization_id UUID NOT NULL,
  data_package_id UUID NOT NULL,
  version INTEGER NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'draft',
  created_by UUID NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_data_package_versions_package_version
    UNIQUE (data_package_id, version),
  CONSTRAINT uq_data_package_versions_id_org
    UNIQUE (id, organization_id),
  CONSTRAINT fk_data_package_versions_package_same_org
    FOREIGN KEY (data_package_id, organization_id)
    REFERENCES data_packages(id, organization_id) ON DELETE RESTRICT,
  CONSTRAINT fk_data_package_versions_created_by
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT,
  CONSTRAINT ck_data_package_versions_version CHECK (version > 0)
);

CREATE INDEX idx_data_package_versions_org ON data_package_versions(organization_id);
CREATE INDEX idx_data_package_versions_package ON data_package_versions(data_package_id);
CREATE INDEX idx_data_package_versions_status ON data_package_versions(status);
CREATE INDEX idx_data_package_versions_created_by ON data_package_versions(created_by);

COMMIT;
