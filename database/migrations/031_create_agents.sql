BEGIN;

CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT uuidv7(),
    organization_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    agent_type VARCHAR(64) NOT NULL,
    description TEXT,
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT fk_agents_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE RESTRICT,
    CONSTRAINT uq_agents_organization_name
        UNIQUE (organization_id, name),
    CONSTRAINT uq_agents_id_organization
        UNIQUE (id, organization_id)
);

CREATE INDEX idx_agents_organization ON agents (organization_id);
CREATE INDEX idx_agents_type ON agents (agent_type);
CREATE INDEX idx_agents_status ON agents (status);

COMMIT;
