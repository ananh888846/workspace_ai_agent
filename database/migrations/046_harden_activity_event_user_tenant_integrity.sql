BEGIN;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM events e
        LEFT JOIN organization_members om
          ON om.organization_id = e.organization_id
         AND om.user_id = e.user_id
        WHERE e.user_id IS NOT NULL AND om.user_id IS NULL
    ) THEN
        RAISE EXCEPTION 'migration 046 blocked: events contains cross-organization user references';
    END IF;

    IF EXISTS (
        SELECT 1 FROM activity_sessions s
        LEFT JOIN organization_members om
          ON om.organization_id = s.organization_id
         AND om.user_id = s.user_id
        WHERE s.user_id IS NOT NULL AND om.user_id IS NULL
    ) THEN
        RAISE EXCEPTION 'migration 046 blocked: activity_sessions contains cross-organization user references';
    END IF;

    IF EXISTS (
        SELECT 1 FROM activities a
        LEFT JOIN organization_members om
          ON om.organization_id = a.organization_id
         AND om.user_id = a.user_id
        WHERE a.user_id IS NOT NULL AND om.user_id IS NULL
    ) THEN
        RAISE EXCEPTION 'migration 046 blocked: activities contains cross-organization user references';
    END IF;
END $$;

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
