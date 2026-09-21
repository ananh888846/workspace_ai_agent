CREATE TABLE anomalies (
  id UUID PRIMARY KEY DEFAULT uuidv7(),
  organization_id UUID NOT NULL,
  anomaly_type VARCHAR(100) NOT NULL,
  severity VARCHAR(32) NOT NULL DEFAULT 'medium',
  status VARCHAR(32) NOT NULL DEFAULT 'open',
  detection_method VARCHAR(100) NOT NULL,
  confidence NUMERIC(5,4),
  user_id UUID,
  device_id UUID,
  resource_id UUID,
  event_id UUID,
  activity_id UUID,
  task_id UUID,
  detected_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at TIMESTAMPTZ,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT ck_anomalies_confidence
    CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1)),
  CONSTRAINT ck_anomalies_resolved_after_detected
    CHECK (resolved_at IS NULL OR resolved_at >= detected_at),
  CONSTRAINT uq_anomalies_id_org UNIQUE (id, organization_id),
  FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE RESTRICT,
  FOREIGN KEY (organization_id, user_id)
    REFERENCES organization_members(organization_id, user_id) ON DELETE RESTRICT,
  FOREIGN KEY (device_id, organization_id)
    REFERENCES devices(id, organization_id) ON DELETE RESTRICT,
  FOREIGN KEY (resource_id, organization_id)
    REFERENCES resources(id, organization_id) ON DELETE RESTRICT,
  FOREIGN KEY (event_id, organization_id)
    REFERENCES events(id, organization_id) ON DELETE RESTRICT,
  FOREIGN KEY (activity_id, organization_id)
    REFERENCES activities(id, organization_id) ON DELETE RESTRICT,
  FOREIGN KEY (task_id, organization_id)
    REFERENCES tasks(id, organization_id) ON DELETE RESTRICT
);

CREATE INDEX idx_anomalies_org_detected ON anomalies (organization_id, detected_at);
CREATE INDEX idx_anomalies_org_status_detected ON anomalies (organization_id, status, detected_at);
CREATE INDEX idx_anomalies_org_severity_detected ON anomalies (organization_id, severity, detected_at);
CREATE INDEX idx_anomalies_org_type_detected ON anomalies (organization_id, anomaly_type, detected_at);
CREATE INDEX idx_anomalies_event ON anomalies (event_id) WHERE event_id IS NOT NULL;
CREATE INDEX idx_anomalies_activity ON anomalies (activity_id) WHERE activity_id IS NOT NULL;
CREATE INDEX idx_anomalies_task ON anomalies (task_id) WHERE task_id IS NOT NULL;
CREATE INDEX idx_anomalies_resource ON anomalies (resource_id) WHERE resource_id IS NOT NULL;
CREATE INDEX idx_anomalies_device ON anomalies (device_id) WHERE device_id IS NOT NULL;
