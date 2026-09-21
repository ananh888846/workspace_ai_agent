BEGIN;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM agent_runs ar
        JOIN conversations c ON c.id = ar.conversation_id
        WHERE ar.conversation_id IS NOT NULL
          AND ar.user_id <> c.user_id
    ) THEN
        RAISE EXCEPTION 'migration 047 blocked: agent_runs contains cross-user conversation references';
    END IF;
END $$;

ALTER TABLE conversations
    ADD CONSTRAINT uq_conversations_id_user
    UNIQUE (id, user_id);

ALTER TABLE agent_runs
    DROP CONSTRAINT IF EXISTS agent_runs_conversation_id_fkey;

ALTER TABLE agent_runs
    ADD CONSTRAINT fk_agent_runs_conversation_user
    FOREIGN KEY (conversation_id, user_id)
    REFERENCES conversations(id, user_id)
    ON DELETE RESTRICT;

COMMIT;
