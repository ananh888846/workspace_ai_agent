BEGIN;

CREATE TABLE permissions (
  id UUID PRIMARY KEY,
  resource VARCHAR(100) NOT NULL,
  action VARCHAR(100) NOT NULL,
  description TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_permissions_resource_action UNIQUE (resource, action)
);
COMMIT;
