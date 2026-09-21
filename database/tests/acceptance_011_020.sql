BEGIN;

CREATE TEMP TABLE acceptance_results (
  test_id TEXT PRIMARY KEY,
  result TEXT NOT NULL
) ON COMMIT DROP;

DO $$
DECLARE
  org_a UUID := uuidv7(); org_b UUID := uuidv7();
  user_a UUID := uuidv7(); user_b UUID := uuidv7();
  account_a UUID := uuidv7(); resource_a UUID := uuidv7(); resource_b UUID := uuidv7();
  package_a UUID := uuidv7(); version_a UUID := uuidv7(); device_a UUID := uuidv7();
  passed BOOLEAN;
BEGIN
  INSERT INTO organizations(id,name,organization_type) VALUES
    (org_a,'AT Org A','test'),(org_b,'AT Org B','test');
  INSERT INTO users(id,name,email) VALUES
    (user_a,'AT User A','at-user-a@example.test'),(user_b,'AT User B','at-user-b@example.test');
  INSERT INTO organization_members(organization_id,user_id,member_role)
  VALUES (org_a,user_a,'owner'),(org_b,user_b,'owner');
  INSERT INTO user_accounts(id,user_id,provider,account_type,external_account_id)
  VALUES (account_a,user_a,'google','gmail','at-account-a');
  INSERT INTO resources(id,organization_id,resource_type,provider,external_id,owner_user_id,name)
  VALUES (resource_a,org_a,'drive_file','google','at-resource-a',user_a,'Resource A'),
         (resource_b,org_b,'drive_file','google','at-resource-b',user_b,'Resource B');
  INSERT INTO data_packages(id,organization_id,owner_user_id,name,package_type)
  VALUES (package_a,org_a,user_a,'Package A','knowledge');
  INSERT INTO data_package_versions(id,organization_id,data_package_id,version,created_by)
  VALUES (version_a,org_a,package_a,1,user_a);
  INSERT INTO devices(id,organization_id,device_uuid,device_type,name)
  VALUES (device_a,org_a,uuidv7(),'esp32','Device A');

  passed := false;
  BEGIN
    INSERT INTO resources(organization_id,parent_resource_id,resource_type,provider,external_id,owner_user_id)
    VALUES (org_a,resource_b,'folder','google','at-parent-cross-org',user_a);
  EXCEPTION WHEN foreign_key_violation THEN passed := true;
  END;
  IF NOT passed THEN RAISE EXCEPTION 'AT-011 failed'; END IF;
  INSERT INTO acceptance_results VALUES ('AT-011','AT-011 PASS');

  passed := false;
  BEGIN
    INSERT INTO resource_permissions(organization_id,resource_id,user_id,action)
    VALUES (org_a,resource_a,user_b,'read');
  EXCEPTION WHEN foreign_key_violation THEN passed := true;
  END;
  IF NOT passed THEN RAISE EXCEPTION 'AT-012 failed'; END IF;
  INSERT INTO acceptance_results VALUES ('AT-012','AT-012 PASS');

  passed := false;
  BEGIN
    INSERT INTO resources(organization_id,resource_type,provider,external_id,user_account_id,owner_user_id)
    VALUES (org_a,'drive_file','facebook','at-provider-mismatch',account_a,user_a);
  EXCEPTION WHEN raise_exception OR foreign_key_violation THEN passed := true;
  END;
  IF NOT passed THEN RAISE EXCEPTION 'AT-013 failed'; END IF;
  INSERT INTO acceptance_results VALUES ('AT-013','AT-013 PASS');

  passed := false;
  BEGIN
    INSERT INTO data_packages(organization_id,owner_user_id,name,package_type)
    VALUES (org_a,user_b,'Bad Package','knowledge');
  EXCEPTION WHEN foreign_key_violation THEN passed := true;
  END;
  IF NOT passed THEN RAISE EXCEPTION 'AT-014 failed'; END IF;
  INSERT INTO acceptance_results VALUES ('AT-014','AT-014 PASS');

  passed := false;
  BEGIN
    INSERT INTO data_package_versions(organization_id,data_package_id,version,created_by)
    VALUES (org_b,package_a,2,user_a);
  EXCEPTION WHEN foreign_key_violation THEN passed := true;
  END;
  IF NOT passed THEN RAISE EXCEPTION 'AT-015 failed'; END IF;
  INSERT INTO acceptance_results VALUES ('AT-015','AT-015 PASS');

  passed := false;
  BEGIN
    INSERT INTO data_package_resources(organization_id,package_version_id,resource_id)
    VALUES (org_a,version_a,resource_b);
  EXCEPTION WHEN foreign_key_violation THEN passed := true;
  END;
  IF NOT passed THEN RAISE EXCEPTION 'AT-016 failed'; END IF;
  INSERT INTO acceptance_results VALUES ('AT-016','AT-016 PASS');

  passed := false;
  BEGIN
    INSERT INTO data_package_grants(organization_id,package_version_id,user_id,permission)
    VALUES (org_a,version_a,user_b,'read');
  EXCEPTION WHEN foreign_key_violation THEN passed := true;
  END;
  IF NOT passed THEN RAISE EXCEPTION 'AT-017 failed'; END IF;
  INSERT INTO acceptance_results VALUES ('AT-017','AT-017 PASS');

  passed := false;
  BEGIN
    INSERT INTO devices(organization_id,resource_id,device_uuid,device_type)
    VALUES (org_a,resource_b,uuidv7(),'esp32');
  EXCEPTION WHEN foreign_key_violation THEN passed := true;
  END;
  IF NOT passed THEN RAISE EXCEPTION 'AT-018 failed'; END IF;
  INSERT INTO acceptance_results VALUES ('AT-018','AT-018 PASS');

  passed := false;
  BEGIN
    INSERT INTO user_sessions(organization_id,user_id,session_token_hash,expires_at)
    VALUES (org_a,uuidv7(),'at-missing-user',now()+interval '1 hour');
  EXCEPTION WHEN foreign_key_violation THEN passed := true;
  END;
  IF NOT passed THEN RAISE EXCEPTION 'AT-019 failed'; END IF;
  INSERT INTO acceptance_results VALUES ('AT-019','AT-019 PASS');

  passed := false;
  BEGIN
    INSERT INTO user_sessions(organization_id,user_id,session_token_hash,device_id,expires_at)
    VALUES (org_a,user_a,'at-cross-org-session',device_a,now()+interval '1 hour');
  EXCEPTION WHEN foreign_key_violation THEN passed := true;
  END;
  IF NOT passed THEN RAISE EXCEPTION 'AT-020 failed'; END IF;
  INSERT INTO acceptance_results VALUES ('AT-020','AT-020 PASS');

  passed := false;
  BEGIN
    INSERT INTO user_sessions(organization_id,user_id,session_token_hash,expires_at,started_at)
    VALUES (org_a,user_a,'at-invalid-session',now()-interval '1 hour',now());
  EXCEPTION WHEN check_violation THEN passed := true;
  END;
  IF NOT passed THEN RAISE EXCEPTION 'AT-021 failed'; END IF;
  INSERT INTO acceptance_results VALUES ('AT-021','AT-021 PASS');

  INSERT INTO device_capabilities(device_id,capability) VALUES (device_a,'camera');
  passed := false;
  BEGIN
    INSERT INTO device_capabilities(device_id,capability) VALUES (device_a,'camera');
  EXCEPTION WHEN unique_violation THEN passed := true;
  END;
  IF NOT passed THEN RAISE EXCEPTION 'AT-022 failed'; END IF;
  INSERT INTO acceptance_results VALUES ('AT-022','AT-022 PASS');
END;
$$;

SELECT test_id AS result FROM acceptance_results ORDER BY test_id;
ROLLBACK;
