CREATE TABLE agent_runs (
  id UUID PRIMARY KEY DEFAULT uuidv7(),
  request_id UUID NOT NULL,
  organization_id UUID NOT NULL,
  user_id UUID NOT NULL,
  agent_id UUID NOT NULL,
  conversation_id UUID,
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at TIMESTAMPTZ,
  status VARCHAR(32) NOT NULL DEFAULT 'running',
  model VARCHAR(100),
  CONSTRAINT ck_agent_runs_finished_after_started
    CHECK (finished_at IS NULL OR finished_at >= started_at),
  CONSTRAINT uq_agent_runs_id_org UNIQUE (id, organization_id),
  FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE RESTRICT,
  FOREIGN KEY (organization_id, user_id)
    REFERENCES organization_members(organization_id, user_id) ON DELETE RESTRICT,
  FOREIGN KEY (agent_id, organization_id)
    REFERENCES agents(id, organization_id) ON DELETE RESTRICT,
  FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE RESTRICT
);

CREATE INDEX idx_agent_runs_request_id ON agent_runs (request_id);
CREATE INDEX idx_agent_runs_org_started ON agent_runs (organization_id, started_at);
CREATE INDEX idx_agent_runs_org_user_started ON agent_runs (organization_id, user_id, started_at);
CREATE INDEX idx_agent_runs_org_status_started ON agent_runs (organization_id, status, started_at);
CREATE INDEX idx_agent_runs_agent_id ON agent_runs (agent_id);
