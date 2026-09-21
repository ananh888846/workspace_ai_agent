BEGIN;

CREATE TABLE user_sessions (
  id UUID PRIMARY KEY DEFAULT uuidv7(),
  organization_id UUID NOT NULL,
  user_id UUID NOT NULL,
  session_token_hash VARCHAR(255) NOT NULL,
  device_id UUID,
  ip_address INET,
  user_agent TEXT,
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ NOT NULL,
  last_activity_at TIMESTAMPTZ,
  revoked_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_user_sessions_token_hash UNIQUE (session_token_hash),
  CONSTRAINT fk_user_sessions_org
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE RESTRICT,
  CONSTRAINT fk_user_sessions_user_member
    FOREIGN KEY (organization_id, user_id)
    REFERENCES organization_members(organization_id, user_id) ON DELETE RESTRICT,
  CONSTRAINT fk_user_sessions_device_same_org
    FOREIGN KEY (device_id, organization_id)
    REFERENCES devices(id, organization_id) ON DELETE RESTRICT,
  CONSTRAINT ck_user_sessions_expiry CHECK (expires_at >= started_at)
);

CREATE INDEX idx_user_sessions_org ON user_sessions(organization_id);
CREATE INDEX idx_user_sessions_user ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_device ON user_sessions(device_id);
CREATE INDEX idx_user_sessions_expires ON user_sessions(expires_at);
CREATE INDEX idx_user_sessions_last_activity ON user_sessions(last_activity_at);

COMMIT;
