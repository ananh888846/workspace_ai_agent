BEGIN;

CREATE TABLE memories (
    id UUID PRIMARY KEY DEFAULT uuidv7(),
    user_id UUID NOT NULL,
    memory_type VARCHAR(64) NOT NULL,
    content TEXT NOT NULL,
    importance NUMERIC(5,4),
    source_conversation_id UUID,
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT fk_memories_user
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT fk_memories_source_conversation
        FOREIGN KEY (source_conversation_id) REFERENCES conversations(id) ON DELETE RESTRICT,
    CONSTRAINT ck_memories_importance
        CHECK (importance IS NULL OR importance BETWEEN 0 AND 1)
);

CREATE INDEX idx_memories_user_status_updated ON memories (user_id, status, updated_at);

COMMIT;
