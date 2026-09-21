# Workspace AI Agent — MIGRATION 051 SCHEMA REVIEW

> Ngày review: 2026-09-21
>
> Trạng thái: **SCHEMA DESIGN LOCKED → SQL IMPLEMENTED → RUNTIME VERIFIED → GATE CLOSED**
>
> Phạm vi: Knowledge Source / Provenance / Document Version / Asset Storage / Chunk / Qdrant mapping.

## 1. Kết luận

Migration 051 là migration hậu V2.1 và không sửa ngược 001 → 050.

Schema đã chốt theo mô hình:

`knowledge_sources → knowledge_documents → knowledge_document_versions → assets/chunks → Qdrant`

với `knowledge_document_version_sources` làm provenance many-to-many.

Knowledge V1 là **provider-neutral và multi-source**. Google Drive chỉ là provider đầu tiên. Schema không tạo bảng knowledge riêng cho Facebook/Meta, Instagram, TikTok, Gmail, Zalo hoặc provider tương lai.

## 2. Design lock

Đã khóa 4 policy:

1. **Content:** canonical normalized text và chunk content dùng PostgreSQL `TEXT`; binary video/image/document/audio dùng File Storage.
2. **Source chưa có resource:** `resource_id = NULL`, status `unresolved`; không bypass authorization.
3. **Derived knowledge:** nhiều source qua `knowledge_document_version_sources`, relation `primary | derived | supporting`.
4. **Retention:** giữ lịch sử version/asset metadata; không hard-delete cascade trong 051.

## 3. Production implementation

Đã triển khai:

- `migrations/051_knowledge_v1.sql`
- `database/tests/acceptance_051.sql`
- `docs/MIGRATION_051_ACCEPTANCE.md`

Migration 051:

- thêm source/provenance;
- thêm document version;
- thêm multi-source mapping;
- thêm binary asset metadata;
- chuyển chunk sang version;
- thêm tenant/composite FK;
- thêm account/provider context check;
- backfill dữ liệu 029/030;
- giữ legacy columns để tương thích trong giai đoạn chuyển tiếp.

## 4. Backfill safety

Nếu legacy `knowledge_documents.organization_id` không resolve được từ `resource_id`, migration dừng.

Legacy version không phải số vẫn được map thành version `1`; canonical content không được tự tạo. Version legacy không có content được đánh dấu `rebuild_required`.

Legacy chunk phải map được tenant + document version; nếu không migration dừng.

## 5. Acceptance gate

Các acceptance case chính:

- source identity duplicate → reject;
- account khác tenant → reject;
- document + checksum duplicate → reject;
- changed checksum → version mới;
- primary/derived/supporting provenance;
- binary asset chỉ giữ storage reference;
- chunk gắn document version;
- cross-tenant provenance → reject.

## 6. Verification status

**SQL prepared:** PASS — baseline 001–050 đã được runtime xác nhận có 45 bảng; Migration 051 không tạo lại index `idx_knowledge_chunks_content_hash` đã có từ Migration 030.

**Acceptance SQL prepared:** PASS — đã bổ sung kiểm tra multi-source provenance thực tế.

**PostgreSQL runtime verification:** PASS — database sạch đã chạy Migration 001–050 thành công (45 bảng), Migration 051 đã áp dụng thành công và acceptance AT-051-01..11 đã PASS với ROLLBACK.

```bash
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f migrations/051_knowledge_v1.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f database/tests/acceptance_051.sql
```

Migration 051 đã đóng gate runtime.

## 7. Next gate

`Migration 051 Gate CLOSED → Knowledge Ingestion V1 runtime integration`

