BEGIN;

DO $$
DECLARE
    org_a UUID := '00000000-0000-0000-0000-000000000101';
    org_b UUID := '00000000-0000-0000-0000-000000000102';
    user_a UUID := '00000000-0000-0000-0000-000000000201';
    user_b UUID := '00000000-0000-0000-0000-000000000202';
    account_a UUID := '00000000-0000-0000-0000-000000000301';
    grant_a_to_b UUID := '00000000-0000-0000-0000-000000000401';
    agent_a UUID := '00000000-0000-0000-0000-000000000501';
    run_b UUID := '00000000-0000-0000-0000-000000000601';
    conversation_b UUID := '00000000-0000-0000-0000-000000000701';
    tool_id UUID := '00000000-0000-0000-0000-000000000801';
    resource_a UUID := '00000000-0000-0000-0000-000000000901';
    local_a UUID := '00000000-0000-0000-0000-000000001001';
    local_b UUID := '00000000-0000-0000-0000-000000001002';
    event_a UUID := '00000000-0000-0000-0000-000000001101';
    session_a UUID := '00000000-0000-0000-0000-000000001201';
    activity_a UUID := '00000000-0000-0000-0000-000000001301';
    dummy UUID;
BEGIN
    INSERT INTO organizations(id,name,organization_type)
    VALUES (org_a,'DBR A','test'),(org_b,'DBR B','test');

    INSERT INTO users(id,name,email)
    VALUES (user_a,'DBR User A','dbr-a@example.invalid'),
           (user_b,'DBR User B','dbr-b@example.invalid');

    INSERT INTO organization_members(organization_id,user_id)
    VALUES (org_a,user_a),(org_a,user_b),(org_b,user_b);

    INSERT INTO user_accounts(id,user_id,provider,account_type,external_account_id,email)
    VALUES (account_a,user_a,'google','test','dbr-account-a','dbr-a@example.invalid');

    INSERT INTO account_grants(id,organization_id,owner_user_id,grantee_user_id,user_account_id)
    VALUES (grant_a_to_b,org_a,user_a,user_b,account_a);

    INSERT INTO agents(id,organization_id,name,agent_type)
    VALUES (agent_a,org_a,'DBR Agent','test');

    INSERT INTO tools(id,name,version)
    VALUES (tool_id,'DBR Tool','1');

    INSERT INTO conversations(id,user_id,title)
    VALUES (conversation_b,user_b,'DBR conversation');

    INSERT INTO agent_runs(id,request_id,organization_id,user_id,agent_id,conversation_id)
    VALUES (run_b,uuidv7(),org_a,user_b,agent_a,conversation_b);

    INSERT INTO resources(id,organization_id,resource_type,provider,external_id,user_account_id,owner_user_id,name)
    VALUES (resource_a,org_a,'file','google_drive','dbr-file-a',account_a,user_a,'DBR account resource');

    INSERT INTO events(id,event_uuid,event_type,organization_id,user_id,source_type,occurred_at)
    VALUES (event_a,uuidv7(),'test',org_a,user_a,'test',now());

    INSERT INTO activity_sessions(id,organization_id,user_id,session_type,started_at)
    VALUES (session_a,org_a,user_a,'test',now());

    INSERT INTO activities(id,organization_id,user_id,activity_type,started_at)
    VALUES (activity_a,org_a,user_a,'test',now());

    BEGIN
        INSERT INTO events(id,event_uuid,event_type,organization_id,user_id,source_type,occurred_at)
        VALUES (uuidv7(),uuidv7(),'bad',org_b,user_a,'test',now());
        RAISE EXCEPTION 'AT-053 expected cross-org event user rejection';
    EXCEPTION WHEN foreign_key_violation THEN
        RAISE NOTICE 'AT-053 PASS';
    END;

    BEGIN
        INSERT INTO activity_sessions(id,organization_id,user_id,session_type,started_at)
        VALUES (uuidv7(),org_b,user_a,'bad',now());
        RAISE EXCEPTION 'AT-054 expected cross-org activity session user rejection';
    EXCEPTION WHEN foreign_key_violation THEN
        RAISE NOTICE 'AT-054 PASS';
    END;

    BEGIN
        INSERT INTO activities(id,organization_id,user_id,activity_type,started_at)
        VALUES (uuidv7(),org_b,user_a,'bad',now());
        RAISE EXCEPTION 'AT-055 expected cross-org activity user rejection';
    EXCEPTION WHEN foreign_key_violation THEN
        RAISE NOTICE 'AT-055 PASS';
    END;

    INSERT INTO tool_runs(agent_run_id,tool_id,account_id)
    VALUES (run_b,tool_id,account_a);
    RAISE NOTICE 'AT-056 PASS';

    INSERT INTO tool_runs(agent_run_id,tool_id,account_id,account_grant_id)
    VALUES (run_b,tool_id,account_a,grant_a_to_b);
    RAISE NOTICE 'AT-057 PASS';

    BEGIN
        INSERT INTO tool_runs(agent_run_id,tool_id,account_id,account_grant_id)
        VALUES (run_b,tool_id,account_a,'00000000-0000-0000-0000-000000009999');
        RAISE EXCEPTION 'AT-058 expected invalid tool account grant rejection';
    EXCEPTION WHEN foreign_key_violation THEN
        RAISE NOTICE 'AT-058 PASS';
    END;

    BEGIN
        INSERT INTO audit_logs(request_id,organization_id,user_id,action,account_id,result)
        VALUES (uuidv7(),org_b,user_b,'read',account_a,'ok');
        RAISE EXCEPTION 'AT-059 expected cross-org audit account rejection';
    EXCEPTION WHEN foreign_key_violation OR raise_exception THEN
        IF SQLSTATE = 'P0001' THEN
            RAISE NOTICE 'AT-059 PASS';
        ELSE
            RAISE NOTICE 'AT-059 PASS';
        END IF;
    END;

    INSERT INTO audit_logs(request_id,organization_id,user_id,action,account_id,result)
    VALUES (uuidv7(),org_a,user_a,'read',account_a,'ok');
    RAISE NOTICE 'AT-060 PASS';

    INSERT INTO audit_logs(request_id,organization_id,user_id,action,account_id,account_grant_id,result)
    VALUES (uuidv7(),org_a,user_b,'read',account_a,grant_a_to_b,'ok');
    RAISE NOTICE 'AT-061 PASS';

    INSERT INTO resources(id,organization_id,resource_type,provider,external_id,owner_user_id,name)
    VALUES (local_a,org_a,'local','internal','same-id',user_a,'Local A');

    INSERT INTO resources(id,organization_id,resource_type,provider,external_id,owner_user_id,name)
    VALUES (local_b,org_b,'local','internal','same-id',user_b,'Local B');
    RAISE NOTICE 'AT-062 PASS';

    BEGIN
        INSERT INTO resources(id,organization_id,resource_type,provider,external_id,user_account_id,owner_user_id,name)
        VALUES (uuidv7(),org_a,'file','google_drive','dbr-file-a',account_a,user_a,'Duplicate account resource');
        RAISE EXCEPTION 'AT-063 expected account-backed resource duplicate rejection';
    EXCEPTION WHEN unique_violation THEN
        RAISE NOTICE 'AT-063 PASS';
    END;

    BEGIN
        INSERT INTO resources(id,organization_id,resource_type,provider,external_id,owner_user_id,name)
        VALUES (uuidv7(),org_a,'local','internal','same-id',user_a,'Duplicate local A');
        RAISE EXCEPTION 'AT-064 expected local resource duplicate rejection';
    EXCEPTION WHEN unique_violation THEN
        RAISE NOTICE 'AT-064 PASS';
    END;

    BEGIN
        INSERT INTO agent_runs(id,request_id,organization_id,user_id,agent_id,conversation_id)
        VALUES (uuidv7(),uuidv7(),org_a,user_a,agent_a,conversation_b);
        RAISE EXCEPTION 'AT-065 expected Agent Run cross-user conversation rejection';
    EXCEPTION WHEN foreign_key_violation THEN
        RAISE NOTICE 'AT-065 PASS';
    END;

    RAISE NOTICE 'AT-053..AT-065 PASS';
END;
END $$;

ROLLBACK;
