BEGIN;

CREATE TABLE data_package_resources (
  id UUID PRIMARY KEY DEFAULT uuidv7(),
  organization_id UUID NOT NULL,
  package_version_id UUID NOT NULL,
  resource_id UUID NOT NULL,
  access_mode VARCHAR(32) NOT NULL DEFAULT 'read',
  CONSTRAINT uq_data_package_resources_package_resource
    UNIQUE (package_version_id, resource_id),
  CONSTRAINT uq_data_package_resources_id_org
    UNIQUE (id, organization_id),
  CONSTRAINT fk_data_package_resources_org
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE RESTRICT,
  CONSTRAINT fk_data_package_resources_version_same_org
    FOREIGN KEY (package_version_id, organization_id)
    REFERENCES data_package_versions(id, organization_id) ON DELETE CASCADE,
  CONSTRAINT fk_data_package_resources_resource_same_org
    FOREIGN KEY (resource_id, organization_id)
    REFERENCES resources(id, organization_id) ON DELETE CASCADE
);

CREATE INDEX idx_data_package_resources_org ON data_package_resources(organization_id);
CREATE INDEX idx_data_package_resources_version ON data_package_resources(package_version_id);
CREATE INDEX idx_data_package_resources_resource ON data_package_resources(resource_id);

COMMIT;
