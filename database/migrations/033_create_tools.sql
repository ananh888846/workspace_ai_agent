BEGIN;

CREATE TABLE tools (
    id UUID PRIMARY KEY DEFAULT uuidv7(),
    name VARCHAR(255) NOT NULL,
    provider VARCHAR(64),
    version VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_tools_name
        UNIQUE (name)
);

CREATE INDEX idx_tools_provider ON tools (provider);
CREATE INDEX idx_tools_status ON tools (status);

COMMIT;
