CREATE TABLE audit_logs (
  id UUID PRIMARY KEY DEFAULT uuidv7(),
  request_id UUID NOT NULL,
  organization_id UUID,
  user_id UUID,
  device_id UUID,
  capability VARCHAR(100),
  action VARCHAR(100) NOT NULL,
  resource_type VARCHAR(100),
  resource_id UUID,
  account_id UUID,
  package_version_id UUID,
  result VARCHAR(32) NOT NULL,
  ip_address INET,
  user_agent TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE RESTRICT,
  FOREIGN KEY (organization_id, user_id)
    REFERENCES organization_members(organization_id, user_id) ON DELETE RESTRICT,
  FOREIGN KEY (device_id, organization_id)
    REFERENCES devices(id, organization_id) ON DELETE RESTRICT,
  FOREIGN KEY (resource_id, organization_id)
    REFERENCES resources(id, organization_id) ON DELETE RESTRICT,
  FOREIGN KEY (account_id) REFERENCES user_accounts(id) ON DELETE RESTRICT,
  FOREIGN KEY (package_version_id, organization_id)
    REFERENCES data_package_versions(id, organization_id) ON DELETE RESTRICT
);

CREATE INDEX idx_audit_logs_request_id ON audit_logs (request_id);
CREATE INDEX idx_audit_logs_org_created ON audit_logs (organization_id, created_at);
CREATE INDEX idx_audit_logs_org_action_created ON audit_logs (organization_id, action, created_at);
CREATE INDEX idx_audit_logs_org_result_created ON audit_logs (organization_id, result, created_at);
CREATE INDEX idx_audit_logs_user_created ON audit_logs (user_id, created_at);
CREATE INDEX idx_audit_logs_resource_created ON audit_logs (resource_id, created_at);
CREATE INDEX idx_audit_logs_account_created ON audit_logs (account_id, created_at);

CREATE OR REPLACE FUNCTION reject_audit_log_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE EXCEPTION 'audit_logs is append-only';
END;
$$;

CREATE TRIGGER trg_audit_logs_append_only
BEFORE UPDATE OR DELETE ON audit_logs
FOR EACH ROW
EXECUTE FUNCTION reject_audit_log_mutation();


CREATE OR REPLACE FUNCTION audit_metadata_contains_secret(payload JSONB)
RETURNS BOOLEAN
LANGUAGE plpgsql
IMMUTABLE
AS $$
DECLARE
  item JSONB;
  key_name TEXT;
BEGIN
  IF payload IS NULL THEN
    RETURN false;
  END IF;

  IF jsonb_typeof(payload) = 'object' THEN
    FOR key_name, item IN SELECT key, value FROM jsonb_each(payload) LOOP
      IF lower(key_name) IN (
        'access_token',
        'refresh_token',
        'api_key',
        'apikey',
        'password',
        'private_key',
        'device_secret',
        'client_secret',
        'secret'
      ) THEN
        RETURN true;
      END IF;

      IF jsonb_typeof(item) IN ('object', 'array')
         AND audit_metadata_contains_secret(item) THEN
        RETURN true;
      END IF;
    END LOOP;
  ELSIF jsonb_typeof(payload) = 'array' THEN
    FOR item IN SELECT value FROM jsonb_array_elements(payload) LOOP
      IF audit_metadata_contains_secret(item) THEN
        RETURN true;
      END IF;
    END LOOP;
  END IF;

  RETURN false;
END;
$$;

CREATE OR REPLACE FUNCTION validate_audit_log_metadata()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF audit_metadata_contains_secret(NEW.metadata) THEN
    RAISE EXCEPTION 'audit metadata contains prohibited secret material';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER trg_audit_logs_safe_metadata
BEFORE INSERT OR UPDATE ON audit_logs
FOR EACH ROW
EXECUTE FUNCTION validate_audit_log_metadata();
