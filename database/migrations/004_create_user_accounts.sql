BEGIN;

CREATE TABLE user_accounts (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  provider VARCHAR(64) NOT NULL,
  account_type VARCHAR(64) NOT NULL,
  external_account_id VARCHAR(255) NOT NULL,
  display_name VARCHAR(255),
  email VARCHAR(320),
  status VARCHAR(32) NOT NULL DEFAULT 'active',
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_user_accounts_provider_external UNIQUE (provider, external_account_id),
  CONSTRAINT uq_user_accounts_id_user UNIQUE (id, user_id),
  CONSTRAINT fk_user_accounts_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT
);
CREATE INDEX idx_user_accounts_user ON user_accounts(user_id);
CREATE INDEX idx_user_accounts_provider ON user_accounts(provider);
CREATE INDEX idx_user_accounts_status ON user_accounts(status);
CREATE INDEX idx_user_accounts_created_at ON user_accounts(created_at);
COMMIT;
