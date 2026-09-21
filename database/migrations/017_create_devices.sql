BEGIN;

CREATE TABLE devices (
  id UUID PRIMARY KEY DEFAULT uuidv7(),
  organization_id UUID NOT NULL,
  resource_id UUID,
  device_uuid UUID NOT NULL,
  device_type VARCHAR(64) NOT NULL,
  name VARCHAR(255),
  status VARCHAR(32) NOT NULL DEFAULT 'active',
  firmware_version VARCHAR(100),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_seen_at TIMESTAMPTZ,
  CONSTRAINT uq_devices_id_org UNIQUE (id, organization_id),
  CONSTRAINT uq_devices_device_uuid UNIQUE (device_uuid),
  CONSTRAINT fk_devices_org
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE RESTRICT,
  CONSTRAINT fk_devices_resource_same_org
    FOREIGN KEY (resource_id, organization_id)
    REFERENCES resources(id, organization_id) ON DELETE RESTRICT
);

CREATE INDEX idx_devices_org ON devices(organization_id);
CREATE INDEX idx_devices_resource ON devices(resource_id);
CREATE INDEX idx_devices_type ON devices(device_type);
CREATE INDEX idx_devices_status ON devices(status);
CREATE INDEX idx_devices_last_seen ON devices(last_seen_at);
CREATE INDEX idx_devices_created_at ON devices(created_at);

COMMIT;
