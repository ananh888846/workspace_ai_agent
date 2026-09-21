BEGIN;

-- Migration 051: Knowledge V1
-- Migrations 001-050 remain immutable.
-- PostgreSQL source of truth; Qdrant is retrieval/index only; binary uses StorageService.

ALTER TABLE knowledge_documents ADD COLUMN IF NOT EXISTS organization_id UUID;

UPDATE knowledge_documents kd
SET organization_id = r.organization_id
FROM resources r
WHERE kd.organization_id IS NULL AND kd.resource_id = r.id;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM knowledge_documents WHERE organization_id IS NULL) THEN
    RAISE EXCEPTION 'Migration 051 blocked: legacy knowledge_documents cannot resolve organization_id';
  END IF;
END $$;

ALTER TABLE knowledge_documents ALTER COLUMN organization_id SET NOT NULL;
ALTER TABLE knowledge_documents
  ADD CONSTRAINT uq_knowledge_documents_id_organization UNIQUE (id, organization_id);

CREATE TABLE knowledge_sources (
  id UUID PRIMARY KEY DEFAULT uuidv7(),
  organization_id UUID NOT NULL,
  user_account_id UUID NULL,
  resource_id UUID NULL,
  provider VARCHAR(64) NOT NULL,
  resource_type VARCHAR(100) NOT NULL,
  external_id VARCHAR(255) NOT NULL,
  source_url TEXT NULL,
  canonical_url TEXT NULL,
  source_revision VARCHAR(255) NULL,
  current_checksum VARCHAR(255) NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'active',
  metadata JSONB NOT NULL DEFAULT '{}',
  last_checked_at TIMESTAMPTZ NULL,
  last_changed_at TIMESTAMPTZ NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_knowledge_sources_id_organization UNIQUE (id, organization_id),
  CONSTRAINT fk_knowledge_sources_resource_tenant
    FOREIGN KEY (resource_id, organization_id)
    REFERENCES resources(id, organization_id) ON DELETE RESTRICT,
  CONSTRAINT fk_knowledge_sources_user_account
    FOREIGN KEY (user_account_id) REFERENCES user_accounts(id) ON DELETE RESTRICT,
  CONSTRAINT ck_knowledge_sources_status
    CHECK (status IN ('active','deleted','unavailable','unresolved')),
  CONSTRAINT ck_knowledge_sources_external_id CHECK (length(trim(external_id)) > 0)
);

CREATE UNIQUE INDEX uq_knowledge_sources_account_identity
  ON knowledge_sources(organization_id,user_account_id,provider,resource_type,external_id)
  WHERE user_account_id IS NOT NULL;
CREATE UNIQUE INDEX uq_knowledge_sources_local_identity
  ON knowledge_sources(organization_id,provider,resource_type,external_id)
  WHERE user_account_id IS NULL;
CREATE INDEX idx_knowledge_sources_resource ON knowledge_sources(resource_id);
CREATE INDEX idx_knowledge_sources_account ON knowledge_sources(user_account_id);
CREATE INDEX idx_knowledge_sources_provider_type
  ON knowledge_sources(organization_id,provider,resource_type);
CREATE INDEX idx_knowledge_sources_status_checked
  ON knowledge_sources(status,last_checked_at);

CREATE OR REPLACE FUNCTION check_knowledge_source_account_context()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.user_account_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM user_accounts ua
    JOIN organization_members om
      ON om.user_id=ua.user_id AND om.organization_id=NEW.organization_id
    WHERE ua.id=NEW.user_account_id AND ua.provider=NEW.provider
  ) THEN
    RAISE EXCEPTION 'knowledge source account context invalid: account %, organization %, provider %',
      NEW.user_account_id,NEW.organization_id,NEW.provider;
  END IF;

  IF NEW.resource_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM resources r
    WHERE r.id=NEW.resource_id
      AND r.organization_id=NEW.organization_id
      AND r.provider=NEW.provider
      AND r.resource_type=NEW.resource_type
      AND (r.user_account_id IS NULL OR r.user_account_id=NEW.user_account_id)
  ) THEN
    RAISE EXCEPTION 'knowledge source resource context invalid: resource %, organization %',
      NEW.resource_id,NEW.organization_id;
  END IF;
  RETURN NEW;
END $$;

CREATE TRIGGER trg_knowledge_source_account_context
BEFORE INSERT OR UPDATE OF organization_id,user_account_id,resource_id,provider,resource_type
ON knowledge_sources FOR EACH ROW
EXECUTE FUNCTION check_knowledge_source_account_context();

CREATE TABLE knowledge_document_versions (
  id UUID PRIMARY KEY DEFAULT uuidv7(),
  organization_id UUID NOT NULL,
  knowledge_document_id UUID NOT NULL,
  version_no BIGINT NOT NULL,
  source_revision VARCHAR(255) NULL,
  checksum VARCHAR(255) NOT NULL,
  canonical_content TEXT NULL,
  content_type VARCHAR(100) NOT NULL DEFAULT 'text/plain',
  status VARCHAR(32) NOT NULL DEFAULT 'active',
  metadata JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_knowledge_document_versions_id_organization UNIQUE(id,organization_id),
  CONSTRAINT uq_knowledge_document_versions_number UNIQUE(knowledge_document_id,version_no),
  CONSTRAINT uq_knowledge_document_versions_checksum UNIQUE(knowledge_document_id,checksum),
  CONSTRAINT fk_knowledge_document_versions_document_tenant
    FOREIGN KEY(knowledge_document_id,organization_id)
    REFERENCES knowledge_documents(id,organization_id) ON DELETE RESTRICT,
  CONSTRAINT ck_knowledge_document_versions_number CHECK(version_no>0),
  CONSTRAINT ck_knowledge_document_versions_status
    CHECK(status IN ('active','superseded','deleted','rebuild_required')),
  CONSTRAINT ck_knowledge_document_versions_content
    CHECK(status='rebuild_required' OR canonical_content IS NOT NULL)
);

CREATE INDEX idx_knowledge_document_versions_document
  ON knowledge_document_versions(knowledge_document_id,version_no DESC);
CREATE INDEX idx_knowledge_document_versions_status
  ON knowledge_document_versions(organization_id,status,created_at);
CREATE INDEX idx_knowledge_document_versions_checksum
  ON knowledge_document_versions(checksum);

CREATE TABLE knowledge_document_version_sources (
  organization_id UUID NOT NULL,
  document_version_id UUID NOT NULL,
  source_id UUID NOT NULL,
  relation_type VARCHAR(32) NOT NULL,
  source_revision VARCHAR(255) NULL,
  source_checksum VARCHAR(255) NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY(document_version_id,source_id),
  CONSTRAINT fk_kdvs_version_tenant
    FOREIGN KEY(document_version_id,organization_id)
    REFERENCES knowledge_document_versions(id,organization_id) ON DELETE RESTRICT,
  CONSTRAINT fk_kdvs_source_tenant
    FOREIGN KEY(source_id,organization_id)
    REFERENCES knowledge_sources(id,organization_id) ON DELETE RESTRICT,
  CONSTRAINT ck_kdvs_relation_type
    CHECK(relation_type IN ('primary','derived','supporting'))
);
CREATE INDEX idx_kdvs_source ON knowledge_document_version_sources(source_id);
CREATE INDEX idx_kdvs_relation
  ON knowledge_document_version_sources(organization_id,relation_type);

CREATE TABLE knowledge_assets (
  id UUID PRIMARY KEY DEFAULT uuidv7(),
  organization_id UUID NOT NULL,
  document_version_id UUID NOT NULL,
  asset_type VARCHAR(32) NOT NULL,
  file_name VARCHAR(500) NULL,
  mime_type VARCHAR(255) NOT NULL,
  file_size BIGINT NOT NULL,
  checksum VARCHAR(255) NOT NULL,
  storage_backend VARCHAR(32) NOT NULL,
  storage_key TEXT NOT NULL,
  width INTEGER NULL,
  height INTEGER NULL,
  duration_ms BIGINT NULL,
  metadata JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_knowledge_assets_id_organization UNIQUE(id,organization_id),
  CONSTRAINT fk_knowledge_assets_version_tenant
    FOREIGN KEY(document_version_id,organization_id)
    REFERENCES knowledge_document_versions(id,organization_id) ON DELETE RESTRICT,
  CONSTRAINT ck_knowledge_assets_file_size CHECK(file_size>=0),
  CONSTRAINT ck_knowledge_assets_dimensions
    CHECK((width IS NULL OR width>0) AND (height IS NULL OR height>0)),
  CONSTRAINT ck_knowledge_assets_duration CHECK(duration_ms IS NULL OR duration_ms>=0),
  CONSTRAINT ck_knowledge_assets_storage_key CHECK(length(trim(storage_key))>0)
);
CREATE INDEX idx_knowledge_assets_version ON knowledge_assets(document_version_id);
CREATE INDEX idx_knowledge_assets_checksum ON knowledge_assets(checksum);
CREATE INDEX idx_knowledge_assets_backend_key ON knowledge_assets(storage_backend,storage_key);

ALTER TABLE knowledge_chunks
  ADD COLUMN IF NOT EXISTS organization_id UUID,
  ADD COLUMN IF NOT EXISTS document_version_id UUID,
  ADD COLUMN IF NOT EXISTS content TEXT;

INSERT INTO knowledge_document_versions(
  organization_id,knowledge_document_id,version_no,source_revision,checksum,
  canonical_content,content_type,status,metadata
)
SELECT kd.organization_id,kd.id,
  CASE WHEN kd.version ~ '^[0-9]+$' THEN GREATEST(kd.version::BIGINT,1) ELSE 1 END,
  NULL,kd.checksum,NULL,'text/plain','rebuild_required',
  jsonb_build_object('migration_051','legacy_version_backfill')
FROM knowledge_documents kd
WHERE NOT EXISTS(
  SELECT 1 FROM knowledge_document_versions v WHERE v.knowledge_document_id=kd.id
);

UPDATE knowledge_chunks kc
SET organization_id=kd.organization_id, document_version_id=v.id
FROM knowledge_documents kd
JOIN knowledge_document_versions v
  ON v.knowledge_document_id=kd.id
WHERE kc.organization_id IS NULL
  AND kc.document_id=kd.id
  AND v.version_no=CASE WHEN kd.version ~ '^[0-9]+$' THEN GREATEST(kd.version::BIGINT,1) ELSE 1 END;

DO $$
BEGIN
  IF EXISTS(SELECT 1 FROM knowledge_chunks WHERE organization_id IS NULL OR document_version_id IS NULL) THEN
    RAISE EXCEPTION 'Migration 051 blocked: legacy knowledge_chunks cannot be mapped to a tenant/document version';
  END IF;
END $$;

ALTER TABLE knowledge_chunks
  ALTER COLUMN organization_id SET NOT NULL,
  ALTER COLUMN document_version_id SET NOT NULL;

ALTER TABLE knowledge_chunks
  ADD CONSTRAINT fk_knowledge_chunks_version_tenant
  FOREIGN KEY(document_version_id,organization_id)
  REFERENCES knowledge_document_versions(id,organization_id) ON DELETE RESTRICT;

ALTER TABLE knowledge_chunks
  ADD CONSTRAINT ck_knowledge_chunks_content_or_hash
  CHECK(content IS NOT NULL OR content_hash IS NOT NULL);

ALTER TABLE knowledge_chunks
  DROP CONSTRAINT IF EXISTS uq_knowledge_chunks_document_index;
ALTER TABLE knowledge_chunks
  ADD CONSTRAINT uq_knowledge_chunks_version_index UNIQUE(document_version_id,chunk_index);

CREATE INDEX idx_knowledge_chunks_version ON knowledge_chunks(document_version_id);
CREATE INDEX idx_knowledge_chunks_content_hash ON knowledge_chunks(content_hash);
CREATE INDEX idx_knowledge_chunks_organization ON knowledge_chunks(organization_id);

COMMENT ON COLUMN knowledge_chunks.document_id IS
  'LEGACY compatibility column after 051; canonical parent is document_version_id.';
COMMENT ON COLUMN knowledge_chunks.qdrant_point_id IS
  'Qdrant retrieval/index identifier; PostgreSQL remains source of truth.';

INSERT INTO knowledge_sources(
  organization_id,user_account_id,resource_id,provider,resource_type,external_id,
  source_revision,current_checksum,status,metadata
)
SELECT kd.organization_id,r.user_account_id,r.id,r.provider,r.resource_type,
  COALESCE(kd.source_id,r.external_id),NULL,kd.checksum,
  CASE WHEN kd.status='active' THEN 'active' ELSE 'unavailable' END,
  jsonb_build_object('migration_051','legacy_knowledge_document')
FROM knowledge_documents kd
JOIN resources r ON r.id=kd.resource_id
WHERE NOT EXISTS(
  SELECT 1 FROM knowledge_sources ks
  WHERE ks.organization_id=kd.organization_id
    AND ks.provider=r.provider AND ks.resource_type=r.resource_type
    AND ks.external_id=COALESCE(kd.source_id,r.external_id)
    AND ks.user_account_id IS NOT DISTINCT FROM r.user_account_id
)
ON CONFLICT DO NOTHING;

INSERT INTO knowledge_document_version_sources(
  organization_id,document_version_id,source_id,relation_type,source_revision,source_checksum
)
SELECT kd.organization_id,v.id,ks.id,'primary',ks.source_revision,ks.current_checksum
FROM knowledge_documents kd
JOIN knowledge_document_versions v ON v.knowledge_document_id=kd.id
JOIN resources r ON r.id=kd.resource_id
JOIN knowledge_sources ks
  ON ks.organization_id=kd.organization_id
 AND ks.provider=r.provider AND ks.resource_type=r.resource_type
 AND ks.external_id=COALESCE(kd.source_id,r.external_id)
 AND ks.user_account_id IS NOT DISTINCT FROM r.user_account_id
ON CONFLICT DO NOTHING;

COMMENT ON TABLE knowledge_sources IS
  'Provider-neutral source identity/provenance. Google Drive is only the first provider.';
COMMENT ON TABLE knowledge_document_versions IS
  'Versioned canonical knowledge content; PostgreSQL source of truth.';
COMMENT ON TABLE knowledge_document_version_sources IS
  'Many-to-many provenance; primary/derived/supporting sources.';
COMMENT ON TABLE knowledge_assets IS
  'Binary asset metadata; bytes live behind StorageService.';
COMMENT ON TABLE knowledge_chunks IS
  'Version-scoped chunks; Qdrant is retrieval/index, not source of truth.';

COMMIT;
