BEGIN;

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
