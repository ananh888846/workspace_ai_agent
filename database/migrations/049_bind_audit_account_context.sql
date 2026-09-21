BEGIN;

ALTER TABLE audit_logs
    ADD COLUMN account_grant_id UUID;

ALTER TABLE audit_logs
    ADD CONSTRAINT fk_audit_logs_account_grant
    FOREIGN KEY (account_grant_id, organization_id)
    REFERENCES account_grants(id, organization_id)
    ON DELETE RESTRICT;

ALTER TABLE audit_logs
    ADD CONSTRAINT ck_audit_logs_account_context
    CHECK (
        account_id IS NULL
        OR user_id IS NOT NULL
    );

CREATE OR REPLACE FUNCTION validate_audit_log_account_context()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.account_id IS NULL THEN
        IF NEW.account_grant_id IS NOT NULL THEN
            RAISE EXCEPTION 'account_grant_id requires account_id';
        END IF;
        RETURN NEW;
    END IF;

    IF NEW.organization_id IS NULL OR NEW.user_id IS NULL THEN
        RAISE EXCEPTION 'audit account usage requires organization_id and user_id';
    END IF;

    IF NEW.account_grant_id IS NULL THEN
        PERFORM 1
          FROM user_accounts
         WHERE id = NEW.account_id
           AND user_id = NEW.user_id;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'audit account is not owned by audit user';
        END IF;
    ELSE
        PERFORM 1
          FROM account_grants ag
         WHERE ag.id = NEW.account_grant_id
           AND ag.organization_id = NEW.organization_id
           AND ag.user_account_id = NEW.account_id
           AND ag.grantee_user_id = NEW.user_id
           AND ag.status = 'active'
           AND ag.revoked_at IS NULL
           AND (ag.starts_at IS NULL OR NEW.created_at >= ag.starts_at)
           AND (ag.expires_at IS NULL OR NEW.created_at <= ag.expires_at);

        IF NOT FOUND THEN
            RAISE EXCEPTION 'audit account grant is invalid or inactive';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_audit_logs_account_context
BEFORE INSERT OR UPDATE OF account_id, account_grant_id, organization_id, user_id, created_at
ON audit_logs
FOR EACH ROW
EXECUTE FUNCTION validate_audit_log_account_context();

CREATE INDEX idx_audit_logs_account_grant_created
    ON audit_logs (account_grant_id, created_at)
    WHERE account_grant_id IS NOT NULL;

COMMIT;
