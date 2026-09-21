BEGIN;

DO $$
DECLARE
    org_a UUID := uuidv7();
    org_b UUID := uuidv7();
    agent_a UUID;
    agent_b UUID;
    tool_a UUID;
    failed BOOLEAN;
BEGIN
    INSERT INTO organizations (id, name, organization_type)
    VALUES
        (org_a, 'AT-031-033 Org A', 'test'),
        (org_b, 'AT-031-033 Org B', 'test');

    -- AT-031: agent must be tenant-scoped and organization FK is enforced.
    INSERT INTO agents (organization_id, name, agent_type)
    VALUES (org_a, 'assistant', 'personal')
    RETURNING id INTO agent_a;

    INSERT INTO agents (organization_id, name, agent_type)
    VALUES (org_b, 'assistant', 'personal')
    RETURNING id INTO agent_b;

    -- Same agent name is allowed in different organizations.
    IF agent_a IS NULL OR agent_b IS NULL THEN
        RAISE EXCEPTION 'AT-031 FAIL: agents were not created';
    END IF;
    RAISE NOTICE 'AT-031 PASS';

    -- Same agent name in the same organization must be rejected.
    failed := false;
    BEGIN
        INSERT INTO agents (organization_id, name, agent_type)
        VALUES (org_a, 'assistant', 'worker');
    EXCEPTION WHEN unique_violation THEN
        failed := true;
    END;
    IF NOT failed THEN
        RAISE EXCEPTION 'AT-032 FAIL: duplicate agent name in same organization was accepted';
    END IF;
    RAISE NOTICE 'AT-032 PASS';

    -- Agent capability mapping is unique per agent and cascades with agent deletion.
    INSERT INTO agent_capabilities (agent_id, capability)
    VALUES (agent_a, 'knowledge.read');

    failed := false;
    BEGIN
        INSERT INTO agent_capabilities (agent_id, capability)
        VALUES (agent_a, 'knowledge.read');
    EXCEPTION WHEN unique_violation THEN
        failed := true;
    END;
    IF NOT failed THEN
        RAISE EXCEPTION 'AT-033 FAIL: duplicate agent capability was accepted';
    END IF;

    DELETE FROM agents WHERE id = agent_a;

    IF EXISTS (
        SELECT 1
        FROM agent_capabilities
        WHERE agent_id = agent_a
    ) THEN
        RAISE EXCEPTION 'AT-033 FAIL: agent capability was not cascaded';
    END IF;
    RAISE NOTICE 'AT-033 PASS';

    -- Tools are a global/shared catalog in V2.1.
    INSERT INTO tools (name, provider, version)
    VALUES ('google_drive', 'google', '1.0.0')
    RETURNING id INTO tool_a;

    IF tool_a IS NULL THEN
        RAISE EXCEPTION 'AT-034 FAIL: tool was not created';
    END IF;

    failed := false;
    BEGIN
        INSERT INTO tools (name, provider, version)
        VALUES ('google_drive', 'google', '2.0.0');
    EXCEPTION WHEN unique_violation THEN
        failed := true;
    END;
    IF NOT failed THEN
        RAISE EXCEPTION 'AT-034 FAIL: duplicate global tool name was accepted';
    END IF;
    RAISE NOTICE 'AT-034 PASS';
END $$;

ROLLBACK;
