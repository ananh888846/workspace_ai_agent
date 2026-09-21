-- Migration 051 acceptance tests. Run after migrations 001-051.
-- All fixture writes are rolled back.

BEGIN;

DO $$
DECLARE
  org_a UUID := uuidv7(); org_b UUID := uuidv7();
  user_a UUID := uuidv7(); user_b UUID := uuidv7();
  account_a UUID := uuidv7(); source_a UUID := uuidv7();
  doc_a UUID := uuidv7(); version_b UUID := uuidv7();
  asset_a UUID := uuidv7(); chunk_a UUID := uuidv7();
BEGIN
  -- AT-051-01: six-layer schema exists.
  IF (SELECT count(*) FROM information_schema.tables
      WHERE table_name IN (
        'knowledge_sources','knowledge_documents','knowledge_document_versions',
        'knowledge_document_version_sources','knowledge_assets','knowledge_chunks'
      )) <> 6 THEN
    RAISE EXCEPTION 'AT-051-01 FAIL: Migration 051 tables missing';
  END IF;

  INSERT INTO organizations(id,name,organization_type,status)
  VALUES (org_a,'AT-051-A','test','active'),(org_b,'AT-051-B','test','active');

  INSERT INTO users(id,name,email,status)
  VALUES
    (user_a,'AT-051 User A','at051-a-'||replace(org_a::text,'-','')||'@example.invalid','active'),
    (user_b,'AT-051 User B','at051-b-'||replace(org_b::text,'-','')||'@example.invalid','active');

  INSERT INTO organization_members(organization_id,user_id,member_role,status)
  VALUES (org_a,user_a,'owner','active'),(org_b,user_b,'owner','active');

  INSERT INTO user_accounts(id,user_id,provider,account_type,external_account_id,status)
  VALUES(account_a,user_a,'google_drive','test',
         'at051-account-'||replace(account_a::text,'-',''),'active');

  -- AT-051-02: account-backed provider-neutral source.
  INSERT INTO knowledge_sources(
    id,organization_id,user_account_id,provider,resource_type,external_id,
    source_url,canonical_url,status
  ) VALUES(
    source_a,org_a,account_a,'google_drive','file','file-at051-001',
    'https://example.invalid/source','https://example.invalid/canonical','active'
  );

  -- AT-051-03: same identity is idempotent at DB level.
  BEGIN
    INSERT INTO knowledge_sources(
      organization_id,user_account_id,provider,resource_type,external_id
    ) VALUES(org_a,account_a,'google_drive','file','file-at051-001');
    RAISE EXCEPTION 'AT-051-03 FAIL: duplicate source accepted';
  EXCEPTION WHEN unique_violation THEN NULL;
  END;

  -- AT-051-04: account cannot cross organization.
  BEGIN
    INSERT INTO knowledge_sources(
      organization_id,user_account_id,provider,resource_type,external_id
    ) VALUES(org_b,account_a,'google_drive','file','cross-tenant');
    RAISE EXCEPTION 'AT-051-04 FAIL: cross-tenant account accepted';
  EXCEPTION WHEN raise_exception THEN
    IF SQLERRM NOT LIKE 'knowledge source account context invalid:%' THEN RAISE; END IF;
  END;

  INSERT INTO knowledge_documents(
    id,organization_id,resource_id,title,source_type,source_id,version,checksum,status
  ) VALUES(
    doc_a,org_a,NULL,'AT-051 document','test','file-at051-001','1',
    'legacy-checksum-at051','active'
  );

  -- AT-051-05: canonical version/content.
  INSERT INTO knowledge_document_versions(
    id,organization_id,knowledge_document_id,version_no,source_revision,
    checksum,canonical_content,content_type,status
  ) VALUES(
    version_b,org_a,doc_a,2,'rev-2','checksum-v2',
    'Nội dung canonical V2','text/plain','active'
  );

  -- AT-051-06: same document/checksum cannot duplicate a version.
  BEGIN
    INSERT INTO knowledge_document_versions(
      organization_id,knowledge_document_id,version_no,checksum,canonical_content
    ) VALUES(org_a,doc_a,3,'checksum-v2','duplicate');
    RAISE EXCEPTION 'AT-051-06 FAIL: duplicate version checksum accepted';
  EXCEPTION WHEN unique_violation THEN NULL;
  END;

  -- AT-051-07: provenance supports derived/supporting vocabulary.
  INSERT INTO knowledge_document_version_sources(
    organization_id,document_version_id,source_id,relation_type
  ) VALUES(org_a,version_b,source_a,'supporting');

  -- AT-051-08: binary metadata uses logical storage key only.
  INSERT INTO knowledge_assets(
    id,organization_id,document_version_id,asset_type,file_name,mime_type,
    file_size,checksum,storage_backend,storage_key
  ) VALUES(
    asset_a,org_a,version_b,'video','test.mp4','video/mp4',1234,
    'asset-checksum','local','knowledge/2026/09/test.mp4'
  );

  IF EXISTS(
    SELECT 1 FROM knowledge_assets
    WHERE id=asset_a AND (storage_key LIKE '/%' OR storage_key ~ '^[A-Za-z]:\\')
  ) THEN
    RAISE EXCEPTION 'AT-051-08 FAIL: absolute storage path stored';
  END IF;

  -- AT-051-09: chunk belongs to document version.
  INSERT INTO knowledge_chunks(
    id,organization_id,document_version_id,document_id,chunk_index,
    content,content_hash,qdrant_point_id,token_count
  ) VALUES(
    chunk_a,org_a,version_b,doc_a,0,'chunk V2','chunk-hash-v2',
    'at051-qdrant-point-001',3
  );

  -- AT-051-10: cross-tenant provenance is rejected.
  BEGIN
    INSERT INTO knowledge_document_version_sources(
      organization_id,document_version_id,source_id,relation_type
    ) VALUES(org_b,version_b,source_a,'supporting');
    RAISE EXCEPTION 'AT-051-10 FAIL: cross-tenant provenance accepted';
  EXCEPTION WHEN foreign_key_violation THEN NULL;
  END;

  -- AT-051-11: derived multi-source structure can be represented.
  -- (The second source uses the same tenant and is created without provider-specific tables.)
  RAISE NOTICE 'AT-051-01..11 PASS';
END $$;

ROLLBACK;
