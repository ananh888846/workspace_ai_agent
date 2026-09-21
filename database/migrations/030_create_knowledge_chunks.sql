BEGIN;

CREATE TABLE knowledge_chunks (
    id UUID PRIMARY KEY DEFAULT uuidv7(),
    document_id UUID NOT NULL,
    chunk_index INTEGER NOT NULL,
    content_hash VARCHAR(255) NOT NULL,
    qdrant_point_id VARCHAR(255) NOT NULL,
    token_count INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT fk_knowledge_chunks_document
        FOREIGN KEY (document_id) REFERENCES knowledge_documents(id) ON DELETE RESTRICT,
    CONSTRAINT uq_knowledge_chunks_document_index
        UNIQUE (document_id, chunk_index),
    CONSTRAINT uq_knowledge_chunks_qdrant_point
        UNIQUE (qdrant_point_id),
    CONSTRAINT ck_knowledge_chunks_index
        CHECK (chunk_index >= 0),
    CONSTRAINT ck_knowledge_chunks_tokens
        CHECK (token_count IS NULL OR token_count >= 0)
);

CREATE INDEX idx_knowledge_chunks_document ON knowledge_chunks (document_id);
CREATE INDEX idx_knowledge_chunks_content_hash ON knowledge_chunks (content_hash);

COMMIT;
