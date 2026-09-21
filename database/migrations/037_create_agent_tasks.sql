CREATE TABLE agent_tasks (
  id UUID PRIMARY KEY DEFAULT uuidv7(),
  organization_id UUID NOT NULL,
  parent_agent_task_id UUID,
  request_id UUID NOT NULL,
  created_by_agent_id UUID NOT NULL,
  assigned_agent_id UUID NOT NULL,
  capability VARCHAR(100) NOT NULL,
  action VARCHAR(100) NOT NULL,
  target_resource_id UUID,
  status VARCHAR(32) NOT NULL DEFAULT 'pending',
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  result_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT ck_agent_tasks_finished_after_started
    CHECK (finished_at IS NULL OR started_at IS NULL OR finished_at >= started_at),
  CONSTRAINT uq_agent_tasks_id_org UNIQUE (id, organization_id),
  FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE RESTRICT,
  FOREIGN KEY (parent_agent_task_id, organization_id)
    REFERENCES agent_tasks(id, organization_id) ON DELETE RESTRICT,
  FOREIGN KEY (created_by_agent_id, organization_id)
    REFERENCES agents(id, organization_id) ON DELETE RESTRICT,
  FOREIGN KEY (assigned_agent_id, organization_id)
    REFERENCES agents(id, organization_id) ON DELETE RESTRICT,
  FOREIGN KEY (target_resource_id, organization_id)
    REFERENCES resources(id, organization_id) ON DELETE RESTRICT
);

CREATE INDEX idx_agent_tasks_org_status_created
  ON agent_tasks (organization_id, status, created_at);
CREATE INDEX idx_agent_tasks_org_assigned_status
  ON agent_tasks (organization_id, assigned_agent_id, status);
CREATE INDEX idx_agent_tasks_org_capability_action_status
  ON agent_tasks (organization_id, capability, action, status);
CREATE INDEX idx_agent_tasks_parent ON agent_tasks (parent_agent_task_id)
  WHERE parent_agent_task_id IS NOT NULL;
CREATE INDEX idx_agent_tasks_target_resource ON agent_tasks (target_resource_id)
  WHERE target_resource_id IS NOT NULL;
CREATE INDEX idx_agent_tasks_request_id ON agent_tasks (request_id);
