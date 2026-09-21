BEGIN;

CREATE TABLE resources (
  id UUID PRIMARY KEY DEFAULT uuidv7(),
  organization_id UUID NOT NULL,
  parent_resource_id UUID,
  resource_type VARCHAR(100) NOT NULL,
  provider VARCHAR(64) NOT NULL,
  external_id VARCHAR(255) NOT NULL,
  user_account_id UUID,
  owner_user_id UUID NOT NULL,
  name VARCHAR(500),
  status VARCHAR(32) NOT NULL DEFAULT 'active',
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_resources_id_org UNIQUE (id, organization_id),
  CONSTRAINT uq_resources_provider_account_type_external
    UNIQUE (provider, user_account_id, resource_type, external_id),
  CONSTRAINT fk_resources_org
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE RESTRICT,
  CONSTRAINT fk_resources_owner
    FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE RESTRICT,
  CONSTRAINT fk_resources_account_owner
    FOREIGN KEY (user_account_id, owner_user_id)
    REFERENCES user_accounts(id, user_id) ON DELETE RESTRICT,
  CONSTRAINT fk_resources_parent_same_org
    FOREIGN KEY (parent_resource_id, organization_id)
    REFERENCES resources(id, organization_id) ON DELETE RESTRICT
);

CREATE OR REPLACE FUNCTION validate_resource_account_consistency()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
  account_provider VARCHAR(64);
BEGIN
  IF NEW.user_account_id IS NOT NULL THEN
    SELECT provider
      INTO account_provider
      FROM user_accounts
     WHERE id = NEW.user_account_id
       AND user_id = NEW.owner_user_id;

    IF account_provider IS NULL THEN
      RAISE EXCEPTION 'resource account ownership is invalid';
    END IF;

    IF account_provider <> NEW.provider THEN
      RAISE EXCEPTION 'resource provider must match user account provider';
    END IF;
  END IF;

  RETURN NEW;
END;
$$;

CREATE TRIGGER trg_resources_account_consistency
BEFORE INSERT OR UPDATE OF provider, user_account_id, owner_user_id
ON resources
FOR EACH ROW
EXECUTE FUNCTION validate_resource_account_consistency();

CREATE INDEX idx_resources_org ON resources(organization_id);
CREATE INDEX idx_resources_parent ON resources(parent_resource_id);
CREATE INDEX idx_resources_type ON resources(resource_type);
CREATE INDEX idx_resources_provider ON resources(provider);
CREATE INDEX idx_resources_external_id ON resources(external_id);
CREATE INDEX idx_resources_account ON resources(user_account_id);
CREATE INDEX idx_resources_owner ON resources(owner_user_id);
CREATE INDEX idx_resources_status ON resources(status);
CREATE INDEX idx_resources_created_at ON resources(created_at);

COMMIT;
