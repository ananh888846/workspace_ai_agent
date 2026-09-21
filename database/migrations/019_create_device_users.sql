BEGIN;

CREATE TABLE device_users (
  organization_id UUID NOT NULL,
  device_id UUID NOT NULL,
  user_id UUID NOT NULL,
  relationship VARCHAR(64) NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (organization_id, device_id, user_id),
  CONSTRAINT fk_device_users_device_same_org
    FOREIGN KEY (device_id, organization_id)
    REFERENCES devices(id, organization_id) ON DELETE CASCADE,
  CONSTRAINT fk_device_users_user_member
    FOREIGN KEY (organization_id, user_id)
    REFERENCES organization_members(organization_id, user_id) ON DELETE RESTRICT
);

CREATE INDEX idx_device_users_device ON device_users(device_id);
CREATE INDEX idx_device_users_user ON device_users(user_id);
CREATE INDEX idx_device_users_status ON device_users(status);

COMMIT;
