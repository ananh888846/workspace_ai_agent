BEGIN;

-- Migration 051: Knowledge V1
-- Extends the immutable 001-050 baseline without changing old migrations.
-- PostgreSQL is the source of truth; binary payloads remain in File Storage.

ALTER TABLE knowledge_documents
    ADD COLUMN organization_id UUID;

-- Legacy documents must resolve to a tenant through their resource.
UPDATE knowledge_documents kd
SET organization_id = r.organization_id
FROM resources r
WHERE kd.resource_id = r.id
  AND kd.organization_id IS NULL;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM knowledge_documents
        WHERE organization_id IS NULL
    ) THEN
        RAISE EXCEPTION
            'Migration 051 backfill failed: knowledge_documents without resolvable organization_id exist';
    END IF;
END $$;

ALTER TABLE knowledge_documents
    ALTER COLUMN organization_id SET NOT NULL;

ALTER TABLE knowledge_documents
    ADD CONSTRAINT uq_knowledge_documents_id_org
    UNIQUE (id, organization_id);

ALTER TABLE knowledge_documents
    ADD CONSTRAINT fk_knowledge_documents_org
    FOREIGN KEY (organization_id)
    REFERENCES organizations(id)
    ON DELETE RESTRICT;

CREATE INDEX idx_knowledge_documents_org
    ON knowledge_documents (organization_id);

-- ---------------------------------------------------------------------------
-- 1. First-class source / provenance
-- ---------------------------------------------------------------------------

CREATE TABLE knowledge_sources (
    id UUID PRIMARY KEY DEFAULT uuidv7(),
    organization_id UUID NOT NULL,
    user_account_id UUID,
    resource_id UUID,
    provider VARCHAR(64) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    external_id VARCHAR(255) NOT NULL,
    source_url TEXT,
    canonical_url TEXT,
    source_revision VARCHAR(255),
    source_checksum VARCHAR(255),
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_knowledge_sources_id_org
        UNIQUE (id, organization_id),

    CONSTRAINT fk_knowledge_sources_org
        FOREIGN KEY (organization_id)
        REFERENCES organizations(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_knowledge_sources_account
        FOREIGN KEY (user_account_id)
        REFERENCES user_accounts(id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_knowledge_sources_resource
        FOREIGN KEY (resource_id)
        REFERENCES resources(id)
        ON DELETE RESTRICT,

    CONSTRAINT ck_knowledge_sources_external_id
        CHECK (length(trim(external_id)) > 0)
);

-- Account-backed identity and tenant-only identity are separate because
-- PostgreSQL UNIQUE treats NULLs as distinct.
CREATE UNIQUE INDEX uq_knowledge_sources_account_identity
    ON knowledge_sources (
        organization_id,
        user_account_id,
        provider,
        resource_type,
        external_id
    )
    WHERE user_account_id IS NOT NULL;

CREATE UNIQUE INDEX uq_knowledge_sources_local_identity
    ON knowledge_sources (
        organization_id,
        provider,
        resource_type,
        external_id
    )
    WHERE user_account_id IS NULL;

CREATE INDEX idx_knowledge_sources_org
    ON knowledge_sources (organization_id);

CREATE INDEX idx_knowledge_sources_account
    ON knowledge_sources (user_account_id);

CREATE INDEX idx_knowledge_sources_resource
    ON knowledge_sources (resource_id);

CREATE INDEX idx_knowledge_sources_provider
    ON knowledge_sources (provider);

CREATE INDEX idx_knowledge_sources_revision
    ON knowledge_sources (source_revision);

CREATE OR REPLACE FUNCTION validate_knowledge_source_context()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    account_user_id UUID;
    account_provider VARCHAR(64);
    resource_org_id UUID;
BEGIN
    IF NEW.user_account_id IS NOT NULL THEN
        SELECT ua.user_id, ua.provider
          INTO account_user_id, account_provider
          FROM user_accounts ua
         WHERE ua.id = NEW.user_account_id;

        IF account_user_id IS NULL
           OR NOT EXISTS (
                SELECT 1
                FROM organization_members om
                WHERE om.organization_id = NEW.organization_id
                  AND om.user_id = account_user_id
                  AND om.status = 'active'
           )
           OR account_provider <> NEW.provider
        THEN
            RAISE EXCEPTION
                'knowledge source account context invalid: account_id=%, organization_id=%, provider=%',
                NEW.user_account_id, NEW.organization_id, NEW.provider;
        END IF;
    END IF;

    IF NEW.resource_id IS NOT NULL THEN
        SELECT r.organization_id
          INTO resource_org_id
          FROM resources r
         WHERE r.id = NEW.resource_id;

        IF resource_org_id IS NULL
           OR resource_org_id <> NEW.organization_id
        THEN
            RAISE EXCEPTION
                'knowledge source resource context invalid: resource_id=%, organization_id=%',
                NEW.resource_id, NEW.organization_id;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_knowledge_sources_context
BEFORE INSERT OR UPDATE OF organization_id, user_account_id, resource_id, provider
ON knowledge_sources
FOR EACH ROW
EXECUTE FUNCTION validate_knowledge_source_context();

-- ---------------------------------------------------------------------------
-- 2. Canonical document versions
-- ---------------------------------------------------------------------------

CREATE TABLE knowledge_document_versions (
    id UUID PRIMARY KEY DEFAULT uuidv7(),
    organization_id UUID NOT NULL,
    knowledge_document_id UUID NOT NULL,
    version_no INTEGER NOT NULL,
    source_revision VARCHAR(255),
    checksum VARCHAR(255) NOT NULL,
    canonical_content TEXT,
    content_type VARCHAR(100) NOT NULL DEFAULT 'text/plain',
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_knowledge_document_versions_id_org
        UNIQUE (id, organization_id),

    CONSTRAINT uq_knowledge_document_versions_no
        UNIQUE (knowledge_document_id, version_no),

    CONSTRAINT uq_knowledge_document_versions_checksum
        UNIQUE (knowledge_document_id, checksum),

    CONSTRAINT fk_knowledge_document_versions_document
        FOREIGN KEY (knowledge_document_id, organization_id)
        REFERENCES knowledge_documents(id, organization_id)
        ON DELETE RESTRICT,

    CONSTRAINT ck_knowledge_document_versions_no
        CHECK (version_no > 0)
);

CREATE INDEX idx_knowledge_document_versions_document
    ON knowledge_document_versions (knowledge_document_id);

CREATE INDEX idx_knowledge_document_versions_org
    ON knowledge_document_versions (organization_id);

CREATE INDEX idx_knowledge_document_versions_checksum
    ON knowledge_document_versions (checksum);

CREATE INDEX idx_knowledge_document_versions_status
    ON knowledge_document_versions (status, updated_at);

-- ---------------------------------------------------------------------------
-- 3. Version ↔ source provenance
-- ---------------------------------------------------------------------------

CREATE TABLE knowledge_document_version_sources (
    organization_id UUID NOT NULL,
    document_version_id UUID NOT NULL,
    source_id UUID NOT NULL,
    relation_type VARCHAR(32) NOT NULL,

    PRIMARY KEY (document_version_id, source_id),

    CONSTRAINT fk_knowledge_document_version_sources_version
        FOREIGN KEY (document_version_id, organization_id)
        REFERENCES knowledge_document_versions(id, organization_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_knowledge_document_version_sources_source
        FOREIGN KEY (source_id, organization_id)
        REFERENCES knowledge_sources(id, organization_id)
        ON DELETE RESTRICT,

    CONSTRAINT ck_knowledge_document_version_sources_relation
        CHECK (relation_type IN ('primary', 'derived', 'supporting'))
);

CREATE INDEX idx_knowledge_document_version_sources_source
    ON knowledge_document_version_sources (source_id);

CREATE INDEX idx_knowledge_document_version_sources_org
    ON knowledge_document_version_sources (organization_id);

-- ---------------------------------------------------------------------------
-- 4. Binary asset metadata
-- ---------------------------------------------------------------------------

CREATE TABLE knowledge_assets (
    id UUID PRIMARY KEY DEFAULT uuidv7(),
    organization_id UUID NOT NULL,
    document_version_id UUID NOT NULL,
    asset_type VARCHAR(32) NOT NULL,
    file_name VARCHAR(500),
    mime_type VARCHAR(255),
    file_size BIGINT,
    checksum VARCHAR(255),
    storage_backend VARCHAR(64) NOT NULL,
    storage_key TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_knowledge_assets_id_org
        UNIQUE (id, organization_id),

    CONSTRAINT fk_knowledge_assets_version
        FOREIGN KEY (document_version_id, organization_id)
        REFERENCES knowledge_document_versions(id, organization_id)
        ON DELETE RESTRICT,

    CONSTRAINT ck_knowledge_assets_file_size
        CHECK (file_size IS NULL OR file_size >= 0),

    CONSTRAINT ck_knowledge_assets_storage_key
        CHECK (
            storage_key <> ''
            AND storage_key !~ '^/'
            AND storage_key !~ '^[A-Za-z]:[\\\\/]'
        )
);

CREATE INDEX idx_knowledge_assets_version
    ON knowledge_assets (document_version_id);

CREATE INDEX idx_knowledge_assets_org
    ON knowledge_assets (organization_id);

CREATE INDEX idx_knowledge_assets_checksum
    ON knowledge_assets (checksum);

-- ---------------------------------------------------------------------------
-- 5. Extend chunks to version-scoped canonical content.
-- ---------------------------------------------------------------------------

ALTER TABLE knowledge_chunks
    ADD COLUMN organization_id UUID,
    ADD COLUMN document_version_id UUID,
    ADD COLUMN content TEXT;

-- Create the initial legacy version for every existing document.
-- Non-numeric legacy versions are normalized to version 1 and marked
-- rebuild_required because migration 029 never stored canonical content.
INSERT INTO knowledge_document_versions (
    organization_id,
    knowledge_document_id,
    version_no,
    source_revision,
    checksum,
    canonical_content,
    content_type,
    status
)
SELECT
    kd.organization_id,
    kd.id,
    CASE
        WHEN kd.version ~ '^[0-9]+$' AND kd.version::integer > 0
            THEN kd.version::integer
        ELSE 1
    END,
    NULL,
    kd.checksum,
    NULL,
    'text/plain',
    'rebuild_required'
FROM knowledge_documents kd;

-- Every legacy chunk must resolve to the document tenant and initial version.
UPDATE knowledge_chunks kc
SET
    organization_id = kd.organization_id,
    document_version_id = kdv.id
FROM knowledge_documents kd
JOIN knowledge_document_versions kdv
  ON kdv.knowledge_document_id = kd.id
 AND kdv.organization_id = kd.organization_id
WHERE kc.document_id = kd.id
  AND kc.organization_id IS NULL;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM knowledge_chunks
        WHERE organization_id IS NULL
           OR document_version_id IS NULL
    ) THEN
        RAISE EXCEPTION
            'Migration 051 backfill failed: knowledge_chunks could not resolve tenant/version';
    END IF;
END $$;

ALTER TABLE knowledge_chunks
    ALTER COLUMN organization_id SET NOT NULL,
    ALTER COLUMN document_version_id SET NOT NULL;

ALTER TABLE knowledge_chunks
    ADD CONSTRAINT fk_knowledge_chunks_document_org
    FOREIGN KEY (document_id, organization_id)
    REFERENCES knowledge_documents(id, organization_id)
    ON DELETE RESTRICT;

ALTER TABLE knowledge_chunks
    ADD CONSTRAINT fk_knowledge_chunks_version_org
    FOREIGN KEY (document_version_id, organization_id)
    REFERENCES knowledge_document_versions(id, organization_id)
    ON DELETE RESTRICT;

-- Version-scoped chunk identity replaces the old document-only uniqueness.
ALTER TABLE knowledge_chunks
    DROP CONSTRAINT uq_knowledge_chunks_document_index;

ALTER TABLE knowledge_chunks
    ADD CONSTRAINT uq_knowledge_chunks_version_index
    UNIQUE (document_version_id, chunk_index);

CREATE INDEX idx_knowledge_chunks_org
    ON knowledge_chunks (organization_id);

CREATE INDEX idx_knowledge_chunks_document_version
    ON knowledge_chunks (document_version_id);

-- Do NOT recreate idx_knowledge_chunks_content_hash:
-- Migration 030 already owns that index.

-- ---------------------------------------------------------------------------
-- 6. Backfill legacy source/provenance where a stable legacy identity exists.
-- ---------------------------------------------------------------------------

INSERT INTO knowledge_sources (
    organization_id,
    user_account_id,
    resource_id,
    provider,
    resource_type,
    external_id,
    status
)
SELECT
    kd.organization_id,
    r.user_account_id,
    kd.resource_id,
    kd.source_type,
    COALESCE(r.resource_type, 'legacy'),
    COALESCE(kd.source_id, r.external_id),
    'unresolved'
FROM knowledge_documents kd
LEFT JOIN resources r ON r.id = kd.resource_id
WHERE COALESCE(kd.source_id, r.external_id) IS NOT NULL
ON CONFLICT DO NOTHING;

INSERT INTO knowledge_document_version_sources (
    organization_id,
    document_version_id,
    source_id,
    relation_type
)
SELECT
    kdv.organization_id,
    kdv.id,
    ks.id,
    'primary'
FROM knowledge_document_versions kdv
JOIN knowledge_documents kd
  ON kd.id = kdv.knowledge_document_id
 AND kd.organization_id = kdv.organization_id
JOIN knowledge_sources ks
  ON ks.organization_id = kd.organization_id
 AND ks.external_id = COALESCE(
      kd.source_id,
      (SELECT r.external_id FROM resources r WHERE r.id = kd.resource_id)
    )
 AND ks.provider = kd.source_type
WHERE NOT EXISTS (
    SELECT 1
    FROM knowledge_document_version_sources x
    WHERE x.document_version_id = kdv.id
      AND x.source_id = ks.id
);

COMMENT ON TABLE knowledge_sources IS
    'Provider-neutral source identity and provenance metadata for Knowledge V1.';

COMMENT ON TABLE knowledge_document_versions IS
    'Canonical version history; PostgreSQL source of truth for Knowledge V1 content.';

COMMENT ON TABLE knowledge_document_version_sources IS
    'Many-to-many provenance mapping for primary, derived and supporting sources.';

COMMENT ON TABLE knowledge_assets IS
    'Binary asset metadata and logical storage reference; binary is kept outside PostgreSQL.';

COMMIT;
