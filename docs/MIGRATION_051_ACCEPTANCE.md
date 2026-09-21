# Migration 051 Acceptance — Knowledge V1

> Ngày: 2026-09-21  
> Migration: `051_knowledge_v1.sql`  
> Phạm vi: Knowledge Source / Provenance / Version / Asset / Chunk / Qdrant mapping.

## Gate

Production SQL 051 chỉ được coi là **PASS** khi chạy trên PostgreSQL và acceptance test hoàn tất với transaction `ROLLBACK`.

## Acceptance cases

| ID | Case | Expected |
|---|---|---|
| AT-051-01 | Six knowledge layers exist | PASS |
| AT-051-02 | Account-backed provider-neutral source | PASS |
| AT-051-03 | Same source identity | Duplicate rejected / idempotent |
| AT-051-04 | Account from another organization | REJECT |
| AT-051-05 | Canonical version/content | PASS |
| AT-051-06 | Same document + checksum | Duplicate version rejected |
| AT-051-07 | primary/derived/supporting provenance | PASS |
| AT-051-08 | Binary asset | metadata + logical storage key only |
| AT-051-09 | Chunk | tied to document version |
| AT-051-10 | Cross-tenant provenance | REJECT |
| AT-051-11 | Multi-source derived knowledge | Supported without provider-specific knowledge tables |

## Idempotency contract

`same identity + same revision/checksum → SKIPPED_UNCHANGED`.

`same identity + changed checksum → new document version → chunk/Qdrant reconciliation`.

Database 051 prevents duplicate source identity and duplicate document/checksum version. The application ingestion worker remains responsible for returning the explicit `SKIPPED_UNCHANGED` result and performing Qdrant reconciliation.

## Backfill contract

- Existing 029/030 are not modified.
- Existing logical documents get `organization_id` from `resources`.
- Existing versions without canonical content are marked `rebuild_required`; content is never invented.
- Existing chunks are attached to the initial document version.
- Legacy source fields remain temporarily for compatibility and are no longer canonical.

## PostgreSQL verification

Run:

```bash
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f migrations/051_knowledge_v1.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f database/tests/acceptance_051.sql
```

Then verify:

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_name IN (
  'knowledge_sources',
  'knowledge_documents',
  'knowledge_document_versions',
  'knowledge_document_version_sources',
  'knowledge_assets',
  'knowledge_chunks'
)
ORDER BY table_name;

SELECT conname
FROM pg_constraint
WHERE conrelid IN (
  'knowledge_sources'::regclass,
  'knowledge_documents'::regclass,
  'knowledge_document_versions'::regclass,
  'knowledge_document_version_sources'::regclass,
  'knowledge_assets'::regclass,
  'knowledge_chunks'::regclass
)
ORDER BY conname;
```

**Runtime result (2026-09-21): PASS.** Database sạch đã chạy migrations 001–050, sau đó Migration 051 và acceptance_051.sql. Acceptance trả về AT-051-01..11 PASS và ROLLBACK. Migration 051 acceptance gate đã đóng.


## Runtime verification result — 2026-09-21

- PostgreSQL database được reset về trạng thái sạch trước khi chạy lại migrations.
- Migrations 001–050: **PASS**, tạo 45 bảng baseline.
- Migration 051: **PASS**.
- Acceptance AT-051-01..11: **PASS**.
- Transaction test kết thúc bằng `ROLLBACK`, không giữ fixture.
- Migration 051 acceptance gate: **CLOSED**.
