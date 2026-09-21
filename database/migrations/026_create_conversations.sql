BEGIN;

CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuidv7(),
    user_id UUID NOT NULL,
    session_id UUID,
    title VARCHAR(500),
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT fk_conversations_user
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT fk_conversations_session
        FOREIGN KEY (session_id) REFERENCES user_sessions(id) ON DELETE RESTRICT
);

CREATE INDEX idx_conversations_user_updated ON conversations (user_id, updated_at);

COMMIT;
