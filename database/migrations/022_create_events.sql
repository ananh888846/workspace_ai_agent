BEGIN;

CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT uuidv7(),
    event_uuid UUID NOT NULL UNIQUE,
    event_type VARCHAR(100) NOT NULL,
    organization_id UUID NOT NULL,
    user_id UUID,
    device_id UUID,
    source_type VARCHAR(64) NOT NULL,
    source_id UUID,
    resource_id UUID,
    occurred_at TIMESTAMPTZ NOT NULL,
    confidence NUMERIC(5,4),
    status VARCHAR(32) NOT NULL DEFAULT 'detected',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT fk_events_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE RESTRICT,
    CONSTRAINT fk_events_user
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT fk_events_device_same_org
        FOREIGN KEY (device_id, organization_id) REFERENCES devices(id, organization_id) ON DELETE RESTRICT,
    CONSTRAINT fk_events_resource_same_org
        FOREIGN KEY (resource_id, organization_id) REFERENCES resources(id, organization_id) ON DELETE RESTRICT,
    CONSTRAINT ck_events_confidence
        CHECK (confidence IS NULL OR confidence BETWEEN 0 AND 1),
    CONSTRAINT uq_events_id_org
        UNIQUE (id, organization_id)
);

CREATE INDEX idx_events_org_occurred ON events (organization_id, occurred_at);
CREATE INDEX idx_events_org_type_occurred ON events (organization_id, event_type, occurred_at);
CREATE INDEX idx_events_device_occurred ON events (device_id, occurred_at);
CREATE INDEX idx_events_resource_occurred ON events (resource_id, occurred_at);

COMMIT;
