BEGIN;

DO $$
DECLARE
    org_a UUID := uuidv7();
    org_b UUID := uuidv7();
    user_a UUID := uuidv7();
    user_b UUID := uuidv7();
    device_a UUID := uuidv7();
    device_b UUID := uuidv7();
    resource_a UUID := uuidv7();
    resource_b UUID := uuidv7();
    event_a UUID := uuidv7();
    event_b UUID := uuidv7();
    session_a UUID := uuidv7();
    conversation_a UUID := uuidv7();
    document_a UUID := uuidv7();
    caught BOOLEAN;
BEGIN
    INSERT INTO organizations (id, name, organization_type) VALUES
        (org_a, 'AT-021-030 Org A', 'test'),
        (org_b, 'AT-021-030 Org B', 'test');

    INSERT INTO users (id, name, email) VALUES
        (user_a, 'AT User A', 'at-021-030-a@example.invalid'),
        (user_b, 'AT User B', 'at-021-030-b@example.invalid');

    INSERT INTO organization_members (organization_id, user_id)
    VALUES
        (org_a, user_a),
        (org_b, user_b);

    INSERT INTO devices (id, organization_id, device_uuid, device_type, name)
    VALUES
        (device_a, org_a, uuidv7(), 'test', 'AT Device A'),
        (device_b, org_b, uuidv7(), 'test', 'AT Device B');

    INSERT INTO resources (
        id, organization_id, resource_type, provider, external_id, owner_user_id, name
    ) VALUES
        (resource_a, org_a, 'document', 'test', 'at-resource-a', user_a, 'AT Resource A'),
        (resource_b, org_b, 'document', 'test', 'at-resource-b', user_b, 'AT Resource B');

    -- AT-021: Observation for nonexistent device -> FK REJECT
    caught := false;
    BEGIN
        INSERT INTO observations (
            organization_id, device_id, observation_type
        ) VALUES (org_a, uuidv7(), 'test');
    EXCEPTION WHEN foreign_key_violation THEN
        caught := true;
    END;
    IF NOT caught THEN RAISE EXCEPTION 'AT-021 failed'; END IF;

    -- AT-022: Event with device/resource from another organization -> REJECT
    caught := false;
    BEGIN
        INSERT INTO events (
            event_uuid, event_type, organization_id, device_id, source_type,
            resource_id, occurred_at
        ) VALUES (
            uuidv7(), 'test', org_a, device_b, 'test', resource_b, now()
        );
    EXCEPTION WHEN foreign_key_violation THEN
        caught := true;
    END;
    IF NOT caught THEN RAISE EXCEPTION 'AT-022 failed'; END IF;

    INSERT INTO events (
        id, event_uuid, event_type, organization_id, user_id, device_id,
        source_type, resource_id, occurred_at
    ) VALUES (
        event_a, uuidv7(), 'test', org_a, user_a, device_a,
        'test', resource_a, now()
    );

    INSERT INTO events (
        id, event_uuid, event_type, organization_id, user_id, device_id,
        source_type, resource_id, occurred_at
    ) VALUES (
        event_b, uuidv7(), 'test', org_b, user_b, device_b,
        'test', resource_b, now()
    );

    -- AT-023: Activity Session with cross-tenant resource/event -> REJECT
    caught := false;
    BEGIN
        INSERT INTO activity_sessions (
            id, organization_id, user_id, resource_id, session_type,
            started_at, source_event_id
        ) VALUES (
            uuidv7(), org_a, user_a, resource_b, 'test', now(), event_b
        );
    EXCEPTION WHEN foreign_key_violation THEN
        caught := true;
    END;
    IF NOT caught THEN RAISE EXCEPTION 'AT-023 failed'; END IF;

    INSERT INTO activity_sessions (
        id, organization_id, user_id, resource_id, session_type,
        started_at, source_event_id
    ) VALUES (
        session_a, org_a, user_a, resource_a, 'test', now(), event_a
    );

    -- AT-024: Activity with cross-tenant session/resource/event -> REJECT
    caught := false;
    BEGIN
        INSERT INTO activities (
            organization_id, user_id, activity_type, resource_id,
            started_at, source_event_id, activity_session_id
        ) VALUES (
            org_a, user_a, 'test', resource_b, now(), event_b, session_a
        );
    EXCEPTION WHEN foreign_key_violation THEN
        caught := true;
    END;
    IF NOT caught THEN RAISE EXCEPTION 'AT-024 failed'; END IF;

    -- AT-025: Invalid activity time range -> CHECK REJECT
    caught := false;
    BEGIN
        INSERT INTO activities (
            organization_id, user_id, activity_type, started_at, ended_at
        ) VALUES (
            org_a, user_a, 'test', now(), now() - interval '1 minute'
        );
    EXCEPTION WHEN check_violation THEN
        caught := true;
    END;
    IF NOT caught THEN RAISE EXCEPTION 'AT-025 failed'; END IF;

    INSERT INTO conversations (id, user_id, title)
    VALUES (conversation_a, user_a, 'AT conversation');

    -- AT-026: Message referencing nonexistent conversation -> FK REJECT
    caught := false;
    BEGIN
        INSERT INTO messages (conversation_id, role, content)
        VALUES (uuidv7(), 'user', 'test');
    EXCEPTION WHEN foreign_key_violation THEN
        caught := true;
    END;
    IF NOT caught THEN RAISE EXCEPTION 'AT-026 failed'; END IF;

    -- AT-027: Negative message token count -> CHECK REJECT
    caught := false;
    BEGIN
        INSERT INTO messages (conversation_id, role, content, tokens)
        VALUES (conversation_a, 'user', 'test', -1);
    EXCEPTION WHEN check_violation THEN
        caught := true;
    END;
    IF NOT caught THEN RAISE EXCEPTION 'AT-027 failed'; END IF;

    -- AT-028: Memory importance outside [0,1] -> CHECK REJECT
    caught := false;
    BEGIN
        INSERT INTO memories (
            user_id, memory_type, content, importance
        ) VALUES (user_a, 'test', 'test', 1.1);
    EXCEPTION WHEN check_violation THEN
        caught := true;
    END;
    IF NOT caught THEN RAISE EXCEPTION 'AT-028 failed'; END IF;

    -- AT-029: Knowledge document references nonexistent resource -> FK REJECT
    caught := false;
    BEGIN
        INSERT INTO knowledge_documents (
            resource_id, source_type, source_id, version, checksum
        ) VALUES (uuidv7(), 'test', 'missing', '1', 'at-029');
    EXCEPTION WHEN foreign_key_violation THEN
        caught := true;
    END;
    IF NOT caught THEN RAISE EXCEPTION 'AT-029 failed'; END IF;

    INSERT INTO knowledge_documents (
        id, resource_id, source_type, source_id, version, checksum
    ) VALUES (
        document_a, resource_a, 'test', 'at-doc', '1', 'at-030'
    );

    -- AT-030: Duplicate document chunk index or Qdrant point id -> UNIQUE REJECT
    INSERT INTO knowledge_chunks (
        document_id, chunk_index, content_hash, qdrant_point_id
    ) VALUES (document_a, 0, 'hash-1', 'at-point-030');

    caught := false;
    BEGIN
        INSERT INTO knowledge_chunks (
            document_id, chunk_index, content_hash, qdrant_point_id
        ) VALUES (document_a, 0, 'hash-2', 'at-point-030-2');
    EXCEPTION WHEN unique_violation THEN
        caught := true;
    END;
    IF NOT caught THEN RAISE EXCEPTION 'AT-030 failed'; END IF;

    INSERT INTO knowledge_chunks (
        document_id, chunk_index, content_hash, qdrant_point_id
    ) VALUES (document_a, 1, 'hash-3', 'at-point-030-2');

    caught := false;
    BEGIN
        INSERT INTO knowledge_chunks (
            document_id, chunk_index, content_hash, qdrant_point_id
        ) VALUES (document_a, 2, 'hash-4', 'at-point-030-2');
    EXCEPTION WHEN unique_violation THEN
        caught := true;
    END;
    IF NOT caught THEN RAISE EXCEPTION 'AT-030 qdrant uniqueness failed'; END IF;

    RAISE NOTICE 'AT-021 PASS';
    RAISE NOTICE 'AT-022 PASS';
    RAISE NOTICE 'AT-023 PASS';
    RAISE NOTICE 'AT-024 PASS';
    RAISE NOTICE 'AT-025 PASS';
    RAISE NOTICE 'AT-026 PASS';
    RAISE NOTICE 'AT-027 PASS';
    RAISE NOTICE 'AT-028 PASS';
    RAISE NOTICE 'AT-029 PASS';
    RAISE NOTICE 'AT-030 PASS';
END $$;

ROLLBACK;
