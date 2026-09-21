CREATE TABLE anomaly_evidence (
  id UUID PRIMARY KEY DEFAULT uuidv7(),
  organization_id UUID NOT NULL,
  anomaly_id UUID NOT NULL,
  observation_id UUID,
  event_id UUID,
  activity_session_id UUID,
  activity_id UUID,
  task_id UUID,
  device_id UUID,
  resource_id UUID,
  evidence_role VARCHAR(64) NOT NULL DEFAULT 'supporting',
  weight NUMERIC(5,4),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT ck_anomaly_evidence_exactly_one_source CHECK (
    num_nonnulls(
      observation_id, event_id, activity_session_id, activity_id,
      task_id, device_id, resource_id
    ) = 1
  ),
  CONSTRAINT ck_anomaly_evidence_weight
    CHECK (weight IS NULL OR (weight >= 0 AND weight <= 1)),
  CONSTRAINT uq_anomaly_evidence_id_org UNIQUE (id, organization_id),
  FOREIGN KEY (anomaly_id, organization_id)
    REFERENCES anomalies(id, organization_id) ON DELETE RESTRICT,
  FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE RESTRICT,
  FOREIGN KEY (observation_id, organization_id)
    REFERENCES observations(id, organization_id) ON DELETE RESTRICT,
  FOREIGN KEY (event_id, organization_id)
    REFERENCES events(id, organization_id) ON DELETE RESTRICT,
  FOREIGN KEY (activity_session_id, organization_id)
    REFERENCES activity_sessions(id, organization_id) ON DELETE RESTRICT,
  FOREIGN KEY (activity_id, organization_id)
    REFERENCES activities(id, organization_id) ON DELETE RESTRICT,
  FOREIGN KEY (task_id, organization_id)
    REFERENCES tasks(id, organization_id) ON DELETE RESTRICT,
  FOREIGN KEY (device_id, organization_id)
    REFERENCES devices(id, organization_id) ON DELETE RESTRICT,
  FOREIGN KEY (resource_id, organization_id)
    REFERENCES resources(id, organization_id) ON DELETE RESTRICT
);

CREATE INDEX idx_anomaly_evidence_anomaly_created
  ON anomaly_evidence (anomaly_id, created_at);
CREATE INDEX idx_anomaly_evidence_source_observation
  ON anomaly_evidence (observation_id) WHERE observation_id IS NOT NULL;
CREATE INDEX idx_anomaly_evidence_source_event
  ON anomaly_evidence (event_id) WHERE event_id IS NOT NULL;
CREATE INDEX idx_anomaly_evidence_source_activity_session
  ON anomaly_evidence (activity_session_id) WHERE activity_session_id IS NOT NULL;
CREATE INDEX idx_anomaly_evidence_source_activity
  ON anomaly_evidence (activity_id) WHERE activity_id IS NOT NULL;
CREATE INDEX idx_anomaly_evidence_source_task
  ON anomaly_evidence (task_id) WHERE task_id IS NOT NULL;
CREATE INDEX idx_anomaly_evidence_source_device
  ON anomaly_evidence (device_id) WHERE device_id IS NOT NULL;
CREATE INDEX idx_anomaly_evidence_source_resource
  ON anomaly_evidence (resource_id) WHERE resource_id IS NOT NULL;
