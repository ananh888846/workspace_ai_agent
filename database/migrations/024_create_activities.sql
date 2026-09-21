BEGIN;

CREATE TABLE activities (
    id UUID PRIMARY KEY DEFAULT uuidv7(),
    organization_id UUID NOT NULL,
    user_id UUID,
    activity_type VARCHAR(100) NOT NULL,
    resource_id UUID,
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    confidence NUMERIC(5,4),
    source_event_id UUID,
    activity_session_id UUID,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT fk_activities_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE RESTRICT,
    CONSTRAINT fk_activities_user
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT fk_activities_resource_same_org
        FOREIGN KEY (resource_id, organization_id) REFERENCES resources(id, organization_id) ON DELETE RESTRICT,
    CONSTRAINT fk_activities_event_same_org
        FOREIGN KEY (source_event_id, organization_id) REFERENCES events(id, organization_id) ON DELETE RESTRICT,
    CONSTRAINT fk_activities_session_same_org
        FOREIGN KEY (activity_session_id, organization_id) REFERENCES activity_sessions(id, organization_id) ON DELETE RESTRICT,
    CONSTRAINT ck_activities_ended_at
        CHECK (ended_at IS NULL OR ended_at >= started_at),
    CONSTRAINT ck_activities_confidence
        CHECK (confidence IS NULL OR confidence BETWEEN 0 AND 1),
    CONSTRAINT uq_activities_id_org
        UNIQUE (id, organization_id)
);

CREATE INDEX idx_activities_org_started ON activities (organization_id, started_at);
CREATE INDEX idx_activities_org_type_started ON activities (organization_id, activity_type, started_at);
CREATE INDEX idx_activities_session_started ON activities (activity_session_id, started_at);

COMMIT;
