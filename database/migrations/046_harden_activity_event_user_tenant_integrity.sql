BEGIN;

ALTER TABLE events
    DROP CONSTRAINT fk_events_user;

ALTER TABLE events
    ADD CONSTRAINT fk_events_user_same_org
    FOREIGN KEY (organization_id, user_id)
    REFERENCES organization_members(organization_id, user_id)
    ON DELETE RESTRICT;

ALTER TABLE activity_sessions
    DROP CONSTRAINT fk_activity_sessions_user;

ALTER TABLE activity_sessions
    ADD CONSTRAINT fk_activity_sessions_user_same_org
    FOREIGN KEY (organization_id, user_id)
    REFERENCES organization_members(organization_id, user_id)
    ON DELETE RESTRICT;

ALTER TABLE activities
    DROP CONSTRAINT fk_activities_user;

ALTER TABLE activities
    ADD CONSTRAINT fk_activities_user_same_org
    FOREIGN KEY (organization_id, user_id)
    REFERENCES organization_members(organization_id, user_id)
    ON DELETE RESTRICT;

COMMIT;
