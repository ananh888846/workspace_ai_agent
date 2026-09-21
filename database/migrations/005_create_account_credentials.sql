BEGIN;

CREATE TABLE account_credentials (
  id UUID PRIMARY KEY,
  user_account_id UUID NOT NULL,
  credential_type VARCHAR(64) NOT NULL,
  encrypted_value BYTEA NOT NULL,
  expires_at TIMESTAMPTZ,
  scopes JSONB NOT NULL DEFAULT '[]'::jsonb,
  status VARCHAR(32) NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT fk_account_credentials_account FOREIGN KEY (user_account_id) REFERENCES user_accounts(id) ON DELETE RESTRICT
);
CREATE INDEX idx_account_credentials_account ON account_credentials(user_account_id);
CREATE INDEX idx_account_credentials_expires ON account_credentials(expires_at);
CREATE INDEX idx_account_credentials_status ON account_credentials(status);
COMMIT;
