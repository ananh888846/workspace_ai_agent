CREATE TABLE automation_actions (
  id UUID PRIMARY KEY DEFAULT uuidv7(),
  organization_id UUID NOT NULL,
  automation_id UUID NOT NULL,
  action_type VARCHAR(100) NOT NULL,
  config JSONB NOT NULL DEFAULT '{}'::jsonb,
  CONSTRAINT uq_automation_actions_id_org UNIQUE (id, organization_id),
  FOREIGN KEY (automation_id, organization_id)
    REFERENCES automations(id, organization_id) ON DELETE RESTRICT,
  FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE RESTRICT
);

CREATE INDEX idx_automation_actions_automation ON automation_actions (automation_id);
CREATE INDEX idx_automation_actions_type_automation
  ON automation_actions (action_type, automation_id);
