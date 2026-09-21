BEGIN;

ALTER TABLE agent_runs
    ADD CONSTRAINT uq_agent_runs_id_org_user
    UNIQUE (id, organization_id, user_id);

ALTER TABLE tool_runs
    ADD COLUMN organization_id UUID,
    ADD COLUMN user_id UUID,
    ADD COLUMN account_grant_id UUID;

UPDATE tool_runs tr
SET organization_id = ar.organization_id,
    user_id = ar.user_id
FROM agent_runs ar
WHERE ar.id = tr.agent_run_id;

ALTER TABLE tool_runs
    ALTER COLUMN organization_id SET NOT NULL,
    ALTER COLUMN user_id SET NOT NULL;

ALTER TABLE tool_runs
    ADD CONSTRAINT fk_tool_runs_agent_run_context
    FOREIGN KEY (agent_run_id, organization_id, user_id)
    REFERENCES agent_runs(id, organization_id, user_id)
    ON DELETE RESTRICT;

ALTER TABLE tool_runs
    ADD CONSTRAINT fk_tool_runs_account_owner
    FOREIGN KEY (account_id, user_id)
    REFERENCES user_accounts(id, user_id)
    ON DELETE RESTRICT;

ALTER TABLE tool_runs
    ADD CONSTRAINT fk_tool_runs_account_grant
    FOREIGN KEY (account_grant_id, organization_id)
    REFERENCES account_grants(id, organization_id)
    ON DELETE RESTRICT;

ALTER TABLE tool_runs
    ADD CONSTRAINT ck_tool_runs_account_context
    CHECK (
        account_id IS NULL
        OR user_id IS NOT NULL
    );

CREATE OR REPLACE FUNCTION validate_tool_run_account_context()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    run_started_at TIMESTAMPTZ;
BEGIN
    IF NEW.account_id IS NULL THEN
        IF NEW.account_grant_id IS NOT NULL THEN
            RAISE EXCEPTION 'account_grant_id requires account_id';
        END IF;
        RETURN NEW;
    END IF;

    SELECT started_at
      INTO run_started_at
      FROM agent_runs
     WHERE id = NEW.agent_run_id
       AND organization_id = NEW.organization_id
       AND user_id = NEW.user_id;

    IF run_started_at IS NULL THEN
        RAISE EXCEPTION 'tool run agent execution context is invalid';
    END IF;

    IF NEW.account_grant_id IS NULL THEN
        PERFORM 1
          FROM user_accounts
         WHERE id = NEW.account_id
           AND user_id = NEW.user_id;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'tool run account is not owned by execution user';
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
           AND (ag.starts_at IS NULL OR run_started_at >= ag.starts_at)
           AND (ag.expires_at IS NULL OR run_started_at <= ag.expires_at);

        IF NOT FOUND THEN
            RAISE EXCEPTION 'tool run account grant is invalid or inactive';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_tool_runs_account_context
BEFORE INSERT OR UPDATE OF agent_run_id, account_id, account_grant_id, organization_id, user_id
ON tool_runs
FOR EACH ROW
EXECUTE FUNCTION validate_tool_run_account_context();

CREATE INDEX idx_tool_runs_org_user_started
    ON tool_runs (organization_id, user_id, started_at);

CREATE INDEX idx_tool_runs_account_grant_started
    ON tool_runs (account_grant_id, started_at)
    WHERE account_grant_id IS NOT NULL;

COMMIT;
