BEGIN;

CREATE TABLE activity_sessions (
    id UUID PRIMARY KEY DEFAULT uuidv7(),
    organization_id UUID NOT NULL,
    user_id UUID,
    resource_id UUID,
    session_type VARCHAR(100) NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    confidence NUMERIC(5,4),
    source_event_id UUID,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT fk_activity_sessions_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE RESTRICT,
    CONSTRAINT fk_activity_sessions_user
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT fk_activity_sessions_resource_same_org
        FOREIGN KEY (resource_id, organization_id) REFERENCES resources(id, organization_id) ON DELETE RESTRICT,
    CONSTRAINT fk_activity_sessions_event_same_org
        FOREIGN KEY (source_event_id, organization_id) REFERENCES events(id, organization_id) ON DELETE RESTRICT,
    CONSTRAINT ck_activity_sessions_ended_at
        CHECK (ended_at IS NULL OR ended_at >= started_at),
    CONSTRAINT ck_activity_sessions_duration
        CHECK (duration_seconds IS NULL OR duration_seconds >= 0),
    CONSTRAINT ck_activity_sessions_confidence
        CHECK (confidence IS NULL OR confidence BETWEEN 0 AND 1),
    CONSTRAINT uq_activity_sessions_id_org
        UNIQUE (id, organization_id)
);

CREATE INDEX idx_activity_sessions_org_started ON activity_sessions (organization_id, started_at);
CREATE INDEX idx_activity_sessions_org_status_started ON activity_sessions (organization_id, status, started_at);
CREATE INDEX idx_activity_sessions_user_started ON activity_sessions (user_id, started_at);
CREATE INDEX idx_activity_sessions_resource_started ON activity_sessions (resource_id, started_at);

COMMIT;
