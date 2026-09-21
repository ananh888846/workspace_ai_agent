BEGIN;

CREATE TABLE user_roles (
  user_id UUID NOT NULL,
  role_id UUID NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, role_id),
  CONSTRAINT fk_user_roles_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  CONSTRAINT fk_user_roles_role FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
);
CREATE INDEX idx_user_roles_role ON user_roles(role_id);
COMMIT;
