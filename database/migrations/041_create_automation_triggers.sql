CREATE TABLE automation_triggers (
  id UUID PRIMARY KEY DEFAULT uuidv7(),
  organization_id UUID NOT NULL,
  automation_id UUID NOT NULL,
  event_type VARCHAR(100) NOT NULL,
  conditions JSONB NOT NULL DEFAULT '{}'::jsonb,
  CONSTRAINT uq_automation_triggers_id_org UNIQUE (id, organization_id),
  FOREIGN KEY (automation_id, organization_id)
    REFERENCES automations(id, organization_id) ON DELETE RESTRICT,
  FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE RESTRICT
);

CREATE INDEX idx_automation_triggers_automation ON automation_triggers (automation_id);
CREATE INDEX idx_automation_triggers_event_automation
  ON automation_triggers (event_type, automation_id);
