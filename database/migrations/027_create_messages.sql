BEGIN;

CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuidv7(),
    conversation_id UUID NOT NULL,
    role VARCHAR(32) NOT NULL,
    content TEXT NOT NULL,
    model VARCHAR(100),
    tokens INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT fk_messages_conversation
        FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE RESTRICT,
    CONSTRAINT ck_messages_tokens
        CHECK (tokens IS NULL OR tokens >= 0)
);

CREATE INDEX idx_messages_conversation_created ON messages (conversation_id, created_at);

COMMIT;
