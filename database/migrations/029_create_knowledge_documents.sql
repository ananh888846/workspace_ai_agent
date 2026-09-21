BEGIN;

CREATE TABLE knowledge_documents (
    id UUID PRIMARY KEY DEFAULT uuidv7(),
    resource_id UUID,
    title VARCHAR(500),
    source_type VARCHAR(64) NOT NULL,
    source_id VARCHAR(255),
    version VARCHAR(100) NOT NULL,
    checksum VARCHAR(255) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT fk_knowledge_documents_resource
        FOREIGN KEY (resource_id) REFERENCES resources(id) ON DELETE RESTRICT,
    CONSTRAINT uq_knowledge_documents_source_version_checksum
        UNIQUE (source_type, source_id, version, checksum)
);

CREATE INDEX idx_knowledge_documents_resource ON knowledge_documents (resource_id);
CREATE INDEX idx_knowledge_documents_source ON knowledge_documents (source_type, source_id);
CREATE INDEX idx_knowledge_documents_checksum ON knowledge_documents (checksum);
CREATE INDEX idx_knowledge_documents_status_updated ON knowledge_documents (status, updated_at);

COMMIT;
