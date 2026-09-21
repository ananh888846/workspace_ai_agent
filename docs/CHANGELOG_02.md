# CHANGELOG_02.md

> Changelog continuation for docs/CHANGELOG.md.
>
> Rule: khi changelog hiện tại quá lớn, tạo file kế tiếp theo thứ tự CHANGELOG_03.md, CHANGELOG_04.md...

## 2026-09-21 — Knowledge Ingestion V1 contracts locked
- Thêm docs/KNOWLEDGE_INGESTION_V1.md.
- Thêm docs/KNOWLEDGE_SOURCE_CONTRACT.md.
- Thêm docs/KNOWLEDGE_PIPELINE.md.
- Chốt Google Drive là provider/source đầu tiên; Facebook/Meta, TikTok và Instagram chỉ mở sau Google gate PASS.

## 2026-09-21 — Knowledge storage/provenance architecture locked
- Thêm docs/KNOWLEDGE_STORAGE_PROVENANCE_V1.md.
- Chốt source URL + canonical URL là provenance metadata.
- Chốt canonical content/metadata/version trong PostgreSQL; binary trong File Storage.
- Chốt StorageService để LocalStorage có thể chuyển sang NASStorage.
- Chốt source revision/checksum để phát hiện thay đổi và reconcile version/chunk/Qdrant.
- Migration 051 chưa triển khai.

## 2026-09-21 — Migration 051 schema review
- Thêm docs/MIGRATION_051_SCHEMA_REVIEW.md.
- Review Migration 029–030 và Database V2.1 contracts.
- Xác định gap: source/provenance chưa first-class; document đang trộn identity/version; chunk chưa gắn version; chưa có asset/storage metadata; chưa có canonical content trong SQL.
- Đề xuất 6 lớp schema: knowledge_sources, knowledge_documents, knowledge_document_versions, knowledge_document_version_sources, knowledge_assets và knowledge_chunks gắn document version.
- Chốt PostgreSQL là source of truth, File Storage là binary store, Qdrant là retrieval/index layer.
- Chưa viết production SQL Migration 051 cho đến khi các policy còn mở được chốt.