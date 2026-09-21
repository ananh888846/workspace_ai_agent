CREATE TABLE agent_messages (
  id UUID PRIMARY KEY DEFAULT uuidv7(),
  organization_id UUID NOT NULL,
  sender_agent_id UUID NOT NULL,
  receiver_agent_id UUID NOT NULL,
  agent_task_id UUID,
  message_type VARCHAR(64) NOT NULL,
  payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  status VARCHAR(32) NOT NULL DEFAULT 'pending',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  processed_at TIMESTAMPTZ,
  CONSTRAINT ck_agent_messages_processed_after_created
    CHECK (processed_at IS NULL OR processed_at >= created_at),
  FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE RESTRICT,
  FOREIGN KEY (sender_agent_id, organization_id)
    REFERENCES agents(id, organization_id) ON DELETE RESTRICT,
  FOREIGN KEY (receiver_agent_id, organization_id)
    REFERENCES agents(id, organization_id) ON DELETE RESTRICT,
  FOREIGN KEY (agent_task_id, organization_id)
    REFERENCES agent_tasks(id, organization_id) ON DELETE RESTRICT
);

CREATE INDEX idx_agent_messages_org_created
  ON agent_messages (organization_id, created_at);
CREATE INDEX idx_agent_messages_org_status_created
  ON agent_messages (organization_id, status, created_at);
CREATE INDEX idx_agent_messages_receiver_status_created
  ON agent_messages (receiver_agent_id, status, created_at);
CREATE INDEX idx_agent_messages_task ON agent_messages (agent_task_id)
  WHERE agent_task_id IS NOT NULL;
