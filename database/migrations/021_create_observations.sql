BEGIN;

CREATE TABLE observations (
    id UUID PRIMARY KEY DEFAULT uuidv7(),
    organization_id UUID NOT NULL,
    device_id UUID NOT NULL,
    observation_type VARCHAR(100) NOT NULL,
    raw_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    confidence NUMERIC(5,4),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT fk_observations_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE RESTRICT,
    CONSTRAINT fk_observations_device_same_org
        FOREIGN KEY (device_id, organization_id) REFERENCES devices(id, organization_id) ON DELETE RESTRICT,
    CONSTRAINT ck_observations_confidence
        CHECK (confidence IS NULL OR confidence BETWEEN 0 AND 1),
    CONSTRAINT uq_observations_id_org
        UNIQUE (id, organization_id)
);

CREATE INDEX idx_observations_device_created
    ON observations (device_id, created_at);
CREATE INDEX idx_observations_org_created
    ON observations (organization_id, created_at);

COMMIT;
