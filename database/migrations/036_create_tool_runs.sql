CREATE TABLE tool_runs (
  id UUID PRIMARY KEY DEFAULT uuidv7(),
  agent_run_id UUID NOT NULL,
  tool_id UUID NOT NULL,
  account_id UUID,
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at TIMESTAMPTZ,
  status VARCHAR(32) NOT NULL DEFAULT 'running',
  error TEXT,
  CONSTRAINT ck_tool_runs_finished_after_started
    CHECK (finished_at IS NULL OR finished_at >= started_at),
  FOREIGN KEY (agent_run_id) REFERENCES agent_runs(id) ON DELETE RESTRICT,
  FOREIGN KEY (tool_id) REFERENCES tools(id) ON DELETE RESTRICT,
  FOREIGN KEY (account_id) REFERENCES user_accounts(id) ON DELETE RESTRICT
);

CREATE INDEX idx_tool_runs_agent_started ON tool_runs (agent_run_id, started_at);
CREATE INDEX idx_tool_runs_tool_started ON tool_runs (tool_id, started_at);
CREATE INDEX idx_tool_runs_account_started ON tool_runs (account_id, started_at)
  WHERE account_id IS NOT NULL;
