BEGIN;

CREATE TABLE agent_capabilities (
    agent_id UUID NOT NULL,
    capability VARCHAR(100) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT true,

    CONSTRAINT pk_agent_capabilities
        PRIMARY KEY (agent_id, capability),
    CONSTRAINT fk_agent_capabilities_agent
        FOREIGN KEY (agent_id) REFERENCES agents(id) ON DELETE CASCADE
);

CREATE INDEX idx_agent_capabilities_capability
    ON agent_capabilities (capability);

COMMIT;
