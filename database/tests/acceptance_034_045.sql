BEGIN;

DO $$
DECLARE
  org_a UUID := uuidv7();
  org_b UUID := uuidv7();
  user_a UUID := uuidv7();
  user_b UUID := uuidv7();
  account_a UUID;
  resource_a UUID;
  resource_b UUID;
  device_a UUID;
  agent_a UUID;
  agent_b UUID;
  tool_a UUID;
  agent_run_a UUID;
  agent_task_a UUID;
  automation_a UUID;
  anomaly_a UUID;
  audit_a UUID;
  failed BOOLEAN;
BEGIN
  INSERT INTO organizations (id, name, organization_type)
  VALUES
    (org_a, 'AT-034-045 Org A', 'test'),
    (org_b, 'AT-034-045 Org B', 'test');

  INSERT INTO users (id, name, email)
  VALUES
    (user_a, 'AT User A', 'at034045-a@example.test'),
    (user_b, 'AT User B', 'at034045-b@example.test');

  INSERT INTO organization_members (organization_id, user_id, member_role)
  VALUES
    (org_a, user_a, 'owner'),
    (org_b, user_b, 'owner');

  INSERT INTO user_accounts (id, user_id, provider, account_type, external_account_id)
  VALUES (uuidv7(), user_a, 'google', 'gmail', 'at034045-google-a')
  RETURNING id INTO account_a;

  INSERT INTO resources (
    organization_id, owner_user_id, name, resource_type, provider, external_id, user_account_id
  )
  VALUES
    (org_a, user_a, 'AT Resource A', 'document', 'google', 'at034045-resource-a', account_a)
  RETURNING id INTO resource_a;

  INSERT INTO resources (
    organization_id, owner_user_id, name, resource_type, provider, external_id
  )
  VALUES
    (org_b, user_b, 'AT Resource B', 'document', 'local', 'at034045-resource-b')
  RETURNING id INTO resource_b;

  INSERT INTO devices (organization_id, resource_id, device_uuid, device_type, name)
  VALUES (org_a, resource_a, uuidv7(), 'esp32', 'AT Device A')
  RETURNING id INTO device_a;

  INSERT INTO agents (organization_id, name, agent_type)
  VALUES (org_a, 'AT Agent A', 'assistant')
  RETURNING id INTO agent_a;

  INSERT INTO agents (organization_id, name, agent_type)
  VALUES (org_b, 'AT Agent B', 'assistant')
  RETURNING id INTO agent_b;

  INSERT INTO tools (name, provider, version)
  VALUES ('at034045-tool', 'test', '1.0.0')
  RETURNING id INTO tool_a;

  INSERT INTO agent_capabilities (agent_id, capability, enabled)
  VALUES (agent_a, 'test.execute', true);

  failed := false;
  BEGIN
    INSERT INTO agent_capabilities (agent_id, capability)
    VALUES (agent_a, 'test.execute');
  EXCEPTION WHEN unique_violation THEN
    failed := true;
  END;
  IF NOT failed THEN RAISE EXCEPTION 'AT-041 FAIL: duplicate tool/agent capability accepted'; END IF;
  RAISE NOTICE 'AT-041 PASS';

  INSERT INTO agent_runs (
    request_id, organization_id, user_id, agent_id, started_at, status, model
  )
  VALUES (uuidv7(), org_a, user_a, agent_a, now(), 'running', 'test-model')
  RETURNING id INTO agent_run_a;

  failed := false;
  BEGIN
    INSERT INTO agent_runs (request_id, organization_id, user_id, agent_id)
    VALUES (uuidv7(), org_a, user_a, uuidv7());
  EXCEPTION WHEN foreign_key_violation THEN
    failed := true;
  END;
  IF NOT failed THEN RAISE EXCEPTION 'AT-042 FAIL: invalid Agent Run FK accepted'; END IF;
  RAISE NOTICE 'AT-042 PASS';

  INSERT INTO tool_runs (agent_run_id, tool_id, started_at, status)
  VALUES (agent_run_a, tool_a, now(), 'running');

  failed := false;
  BEGIN
    INSERT INTO tool_runs (agent_run_id, tool_id)
    VALUES (uuidv7(), tool_a);
  EXCEPTION WHEN foreign_key_violation THEN
    failed := true;
  END;
  IF NOT failed THEN RAISE EXCEPTION 'AT-043 FAIL: invalid Tool Run Agent Run FK accepted'; END IF;
  RAISE NOTICE 'AT-043 PASS';

  INSERT INTO agent_tasks (
    organization_id, request_id, created_by_agent_id, assigned_agent_id,
    capability, action, target_resource_id
  )
  VALUES (
    org_a, uuidv7(), agent_a, agent_a, 'test.execute', 'read', resource_a
  )
  RETURNING id INTO agent_task_a;

  failed := false;
  BEGIN
    INSERT INTO agent_tasks (
      organization_id, request_id, created_by_agent_id, assigned_agent_id,
      capability, action, started_at, finished_at
    )
    VALUES (
      org_a, uuidv7(), agent_a, agent_a, 'test.execute', 'read',
      now(), now() - interval '1 minute'
    );
  EXCEPTION WHEN check_violation THEN
    failed := true;
  END;
  IF NOT failed THEN RAISE EXCEPTION 'AT-044 FAIL: invalid Agent Task lifecycle accepted'; END IF;
  RAISE NOTICE 'AT-044 PASS';

  INSERT INTO agent_permissions (
    organization_id, grantor_agent_id, grantee_agent_id,
    capability, action, resource_id, starts_at, expires_at
  )
  VALUES (
    org_a, agent_a, agent_a, 'test.execute', 'read', resource_a,
    now(), now() + interval '1 hour'
  );

  failed := false;
  BEGIN
    INSERT INTO agent_permissions (
      organization_id, grantor_agent_id, grantee_agent_id,
      capability, action, starts_at, expires_at
    )
    VALUES (
      org_a, agent_a, agent_a, 'test.execute', 'read',
      now(), now() - interval '1 minute'
    );
  EXCEPTION WHEN check_violation THEN
    failed := true;
  END;
  IF NOT failed THEN RAISE EXCEPTION 'AT-045 FAIL: invalid Agent Permission expiry accepted'; END IF;
  RAISE NOTICE 'AT-045 PASS';

  INSERT INTO agent_messages (
    organization_id, sender_agent_id, receiver_agent_id,
    agent_task_id, message_type, payload
  )
  VALUES (
    org_a, agent_a, agent_a, agent_task_a, 'test', '{"ok":true}'::jsonb
  );

  failed := false;
  BEGIN
    INSERT INTO agent_messages (
      organization_id, sender_agent_id, receiver_agent_id,
      agent_task_id, message_type
    )
    VALUES (
      org_a, agent_a, agent_a, uuidv7(), 'test'
    );
  EXCEPTION WHEN foreign_key_violation THEN
    failed := true;
  END;
  IF NOT failed THEN RAISE EXCEPTION 'AT-046 FAIL: invalid Agent Message task FK accepted'; END IF;
  RAISE NOTICE 'AT-046 PASS';

  INSERT INTO automations (organization_id, owner_user_id, name)
  VALUES (org_a, user_a, 'AT Automation')
  RETURNING id INTO automation_a;

  failed := false;
  BEGIN
    INSERT INTO automations (organization_id, owner_user_id, name)
    VALUES (org_a, user_b, 'AT Automation Bypass');
  EXCEPTION WHEN foreign_key_violation THEN
    failed := true;
  END;
  IF NOT failed THEN RAISE EXCEPTION 'AT-047 FAIL: automation owner outside organization accepted'; END IF;
  RAISE NOTICE 'AT-047 PASS';

  INSERT INTO automation_triggers (organization_id, automation_id, event_type)
  VALUES (org_a, automation_a, 'test.event');

  INSERT INTO automation_actions (organization_id, automation_id, action_type, config)
  VALUES (org_a, automation_a, 'test.action', '{"mode":"safe"}'::jsonb);

  failed := false;
  BEGIN
    INSERT INTO automation_triggers (organization_id, automation_id, event_type)
    VALUES (org_b, automation_a, 'cross.tenant');
  EXCEPTION WHEN foreign_key_violation THEN
    failed := true;
  END;
  IF NOT failed THEN RAISE EXCEPTION 'AT-048 FAIL: cross-tenant automation child accepted'; END IF;
  RAISE NOTICE 'AT-048 PASS';

  INSERT INTO anomalies (
    organization_id, anomaly_type, detection_method,
    confidence, resource_id
  )
  VALUES (org_a, 'test.anomaly', 'acceptance', 0.75, resource_a)
  RETURNING id INTO anomaly_a;

  failed := false;
  BEGIN
    INSERT INTO anomalies (
      organization_id, anomaly_type, detection_method, resource_id
    )
    VALUES (org_a, 'cross.tenant', 'acceptance', resource_b);
  EXCEPTION WHEN foreign_key_violation THEN
    failed := true;
  END;
  IF NOT failed THEN RAISE EXCEPTION 'AT-049 FAIL: cross-tenant anomaly resource accepted'; END IF;

  BEGIN
    INSERT INTO anomalies (
      organization_id, anomaly_type, detection_method, confidence
    )
    VALUES (org_a, 'bad.confidence', 'acceptance', 1.1);
    RAISE EXCEPTION 'AT-049 FAIL: invalid confidence accepted';
  EXCEPTION WHEN check_violation THEN
    NULL;
  END;
  RAISE NOTICE 'AT-049 PASS';

  INSERT INTO anomaly_evidence (
    organization_id, anomaly_id, resource_id, evidence_role, weight
  )
  VALUES (org_a, anomaly_a, resource_a, 'supporting', 0.8);

  failed := false;
  BEGIN
    INSERT INTO anomaly_evidence (
      organization_id, anomaly_id, resource_id
    )
    VALUES (org_a, anomaly_a, resource_b);
  EXCEPTION WHEN foreign_key_violation THEN
    failed := true;
  END;
  IF NOT failed THEN RAISE EXCEPTION 'AT-050 FAIL: cross-tenant anomaly evidence accepted'; END IF;

  failed := false;
  BEGIN
    INSERT INTO anomaly_evidence (
      organization_id, anomaly_id, resource_id, weight
    )
    VALUES (org_a, anomaly_a, resource_a, 1.1);
  EXCEPTION WHEN check_violation THEN
    failed := true;
  END;
  IF NOT failed THEN RAISE EXCEPTION 'AT-050 FAIL: invalid evidence weight accepted'; END IF;

  INSERT INTO audit_logs (
    request_id, organization_id, user_id, action, resource_id, result, metadata
  )
  VALUES (
    uuidv7(), org_a, user_a, 'test.audit', resource_a, 'success',
    '{"source":"acceptance"}'::jsonb
  )
  RETURNING id INTO audit_a;

  failed := false;
  BEGIN
    INSERT INTO audit_logs (
      request_id, organization_id, user_id, action, resource_id, result
    )
    VALUES (uuidv7(), org_a, user_a, 'bad.audit', uuidv7(), 'failure');
  EXCEPTION WHEN foreign_key_violation THEN
    failed := true;
  END;
  IF NOT failed THEN RAISE EXCEPTION 'AT-051 FAIL: invalid audit resource FK accepted'; END IF;

  BEGIN
    INSERT INTO audit_logs (
      request_id, organization_id, user_id, action, result, metadata
    )
    VALUES (
      uuidv7(), org_a, user_a, 'secret.audit', 'failure',
      '{"access_token":"should-not-be-stored"}'::jsonb
    );
    RAISE EXCEPTION 'AT-051 FAIL: audit secret metadata accepted';
  EXCEPTION WHEN raise_exception THEN
    IF SQLERRM = 'AT-051 FAIL: audit secret metadata accepted' THEN
      RAISE;
    END IF;
  WHEN others THEN
    NULL;
  END;

  failed := false;
  BEGIN
    UPDATE audit_logs SET action = 'mutated' WHERE id = audit_a;
  EXCEPTION WHEN raise_exception THEN
    failed := true;
  END;
  IF NOT failed THEN RAISE EXCEPTION 'AT-052 FAIL: audit UPDATE accepted'; END IF;

  failed := false;
  BEGIN
    DELETE FROM audit_logs WHERE id = audit_a;
  EXCEPTION WHEN raise_exception THEN
    failed := true;
  END;
  IF NOT failed THEN RAISE EXCEPTION 'AT-052 FAIL: audit DELETE accepted'; END IF;

  RAISE NOTICE 'AT-051 PASS';
  RAISE NOTICE 'AT-052 PASS';
END $$;

ROLLBACK;
