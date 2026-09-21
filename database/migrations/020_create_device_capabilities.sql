BEGIN;

CREATE TABLE device_capabilities (
  id UUID PRIMARY KEY DEFAULT uuidv7(),
  device_id UUID NOT NULL,
  capability VARCHAR(100) NOT NULL,
  enabled BOOLEAN NOT NULL DEFAULT true,
  config JSONB NOT NULL DEFAULT '{}'::jsonb,
  CONSTRAINT uq_device_capabilities_device_capability
    UNIQUE (device_id, capability),
  CONSTRAINT fk_device_capabilities_device
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
);

CREATE INDEX idx_device_capabilities_device ON device_capabilities(device_id);
CREATE INDEX idx_device_capabilities_enabled ON device_capabilities(enabled);

COMMIT;
