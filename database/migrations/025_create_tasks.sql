BEGIN;

CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuidv7(),
    organization_id UUID NOT NULL,
    parent_task_id UUID,
    created_by_user_id UUID NOT NULL,
    assigned_user_id UUID,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    task_type VARCHAR(100) NOT NULL,
    priority INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    resource_id UUID,
    source_event_id UUID,
    due_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT fk_tasks_organization
        FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE RESTRICT,
    CONSTRAINT fk_tasks_creator_same_org
        FOREIGN KEY (organization_id, created_by_user_id) REFERENCES organization_members(organization_id, user_id) ON DELETE RESTRICT,
    CONSTRAINT fk_tasks_assignee_same_org
        FOREIGN KEY (organization_id, assigned_user_id) REFERENCES organization_members(organization_id, user_id) ON DELETE RESTRICT,
    CONSTRAINT fk_tasks_parent_same_org
        FOREIGN KEY (parent_task_id, organization_id) REFERENCES tasks(id, organization_id) ON DELETE RESTRICT,
    CONSTRAINT fk_tasks_resource_same_org
        FOREIGN KEY (resource_id, organization_id) REFERENCES resources(id, organization_id) ON DELETE RESTRICT,
    CONSTRAINT fk_tasks_event_same_org
        FOREIGN KEY (source_event_id, organization_id) REFERENCES events(id, organization_id) ON DELETE RESTRICT,
    CONSTRAINT ck_tasks_completed_at
        CHECK (completed_at IS NULL OR started_at IS NULL OR completed_at >= started_at),
    CONSTRAINT ck_tasks_parent_not_self
        CHECK (parent_task_id IS NULL OR parent_task_id <> id),
    CONSTRAINT uq_tasks_id_org
        UNIQUE (id, organization_id)
);

CREATE INDEX idx_tasks_org_status_created ON tasks (organization_id, status, created_at);
CREATE INDEX idx_tasks_org_priority_status ON tasks (organization_id, priority, status);
CREATE INDEX idx_tasks_org_due ON tasks (organization_id, due_at);
CREATE INDEX idx_tasks_parent ON tasks (parent_task_id);

COMMIT;
