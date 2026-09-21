BEGIN;

DO $$
DECLARE
    required_constraint TEXT;
BEGIN
    -- 046
    SELECT conname INTO required_constraint
    FROM pg_constraint
    WHERE conrelid = 'events'::regclass AND conname = 'fk_events_user_same_org';
    IF required_constraint IS NULL THEN RAISE EXCEPTION 'RV-001 FAIL: events tenant FK missing'; END IF;

    SELECT conname INTO required_constraint
    FROM pg_constraint
    WHERE conrelid = 'activity_sessions'::regclass AND conname = 'fk_activity_sessions_user_same_org';
    IF required_constraint IS NULL THEN RAISE EXCEPTION 'RV-002 FAIL: activity_sessions tenant FK missing'; END IF;

    SELECT conname INTO required_constraint
    FROM pg_constraint
    WHERE conrelid = 'activities'::regclass AND conname = 'fk_activities_user_same_org';
    IF required_constraint IS NULL THEN RAISE EXCEPTION 'RV-003 FAIL: activities tenant FK missing'; END IF;

    -- 047
    SELECT conname INTO required_constraint
    FROM pg_constraint
    WHERE conrelid = 'conversations'::regclass AND conname = 'uq_conversations_id_user';
    IF required_constraint IS NULL THEN RAISE EXCEPTION 'RV-004 FAIL: conversation owner key missing'; END IF;

    SELECT conname INTO required_constraint
    FROM pg_constraint
    WHERE conrelid = 'agent_runs'::regclass AND conname = 'fk_agent_runs_conversation_user';
    IF required_constraint IS NULL THEN RAISE EXCEPTION 'RV-005 FAIL: agent run conversation FK missing'; END IF;

    -- 048
    SELECT attname INTO required_constraint FROM pg_attribute
    WHERE attrelid='tool_runs'::regclass AND attname='organization_id' AND NOT attisdropped;
    IF required_constraint IS NULL THEN RAISE EXCEPTION 'RV-006 FAIL: tool_runs.organization_id missing'; END IF;

    SELECT attname INTO required_constraint FROM pg_attribute
    WHERE attrelid='tool_runs'::regclass AND attname='user_id' AND NOT attisdropped;
    IF required_constraint IS NULL THEN RAISE EXCEPTION 'RV-007 FAIL: tool_runs.user_id missing'; END IF;

    SELECT attname INTO required_constraint FROM pg_attribute
    WHERE attrelid='tool_runs'::regclass AND attname='account_grant_id' AND NOT attisdropped;
    IF required_constraint IS NULL THEN RAISE EXCEPTION 'RV-008 FAIL: tool_runs.account_grant_id missing'; END IF;

    SELECT conname INTO required_constraint
    FROM pg_constraint
    WHERE conrelid='tool_runs'::regclass AND conname='fk_tool_runs_agent_run_context';
    IF required_constraint IS NULL THEN RAISE EXCEPTION 'RV-009 FAIL: tool run execution context FK missing'; END IF;

    SELECT tgname INTO required_constraint
    FROM pg_trigger
    WHERE tgrelid='tool_runs'::regclass AND tgname='trg_tool_runs_account_context' AND NOT tgisinternal;
    IF required_constraint IS NULL THEN RAISE EXCEPTION 'RV-010 FAIL: tool run account trigger missing'; END IF;

    -- 049
    SELECT attname INTO required_constraint FROM pg_attribute
    WHERE attrelid='audit_logs'::regclass AND attname='account_grant_id' AND NOT attisdropped;
    IF required_constraint IS NULL THEN RAISE EXCEPTION 'RV-011 FAIL: audit_logs.account_grant_id missing'; END IF;

    SELECT tgname INTO required_constraint
    FROM pg_trigger
    WHERE tgrelid='audit_logs'::regclass AND tgname='trg_audit_logs_account_context' AND NOT tgisinternal;
    IF required_constraint IS NULL THEN RAISE EXCEPTION 'RV-012 FAIL: audit account trigger missing'; END IF;

    -- 050
    SELECT indexname INTO required_constraint
    FROM pg_indexes
    WHERE tablename='resources' AND indexname='uq_resources_account_identity';
    IF required_constraint IS NULL THEN RAISE EXCEPTION 'RV-013 FAIL: account resource identity index missing'; END IF;

    SELECT indexname INTO required_constraint
    FROM pg_indexes
    WHERE tablename='resources' AND indexname='uq_resources_local_identity';
    IF required_constraint IS NULL THEN RAISE EXCEPTION 'RV-014 FAIL: local resource identity index missing'; END IF;

    RAISE NOTICE 'RV-001..RV-014 PASS';
END $$;

ROLLBACK;
