# CHANGELOG_02.md

> Changelog continuation for docs/CHANGELOG.md.
>
> Rule: Khi một file CHANGELOG trở nên quá lớn, không tiếp tục phình file cũ. Tạo file kế tiếp theo thứ tự CHANGELOG_02.md, CHANGELOG_03.md, CHANGELOG_04.md... và tiếp tục ghi log theo thứ tự thời gian.

## 2026-09-21 — Knowledge Ingestion V1 contracts locked
- Thêm docs/KNOWLEDGE_INGESTION_V1.md: lifecycle, authorization boundary, idempotency, versioning, retry và provider rollout.
- Thêm docs/KNOWLEDGE_SOURCE_CONTRACT.md: canonical source item, identity, account/resource binding, checksum và provider mapping.
- Thêm docs/KNOWLEDGE_PIPELINE.md: Fetch → Normalize → Version → Chunk → Embed → PostgreSQL/Qdrant → Retrieval.
- Chốt Google Drive là provider/source đầu tiên; Facebook/Meta, TikTok và Instagram chỉ mở sau Google gate PASS.
- Chưa thay đổi production schema và chưa viết Agent runtime code.

## 2026-09-21 — Knowledge storage/provenance architecture locked
- Thêm docs/KNOWLEDGE_STORAGE_PROVENANCE_V1.md.
- Chốt source URL và canonical URL là provenance metadata; URL không thay thế identity.
- Chốt lưu nội dung canonical + metadata/version trong PostgreSQL; binary video/image/document/audio lưu qua File Storage.
- Chốt StorageService abstraction: V1 có thể dùng LocalStorage, tương lai chuyển sang NASStorage mà không đổi domain/application contract.
- Chốt asset metadata gồm storage backend/key, MIME, size, checksum và quan hệ với document version.
- Chốt một source có thể có nhiều asset và một derived knowledge item có thể có nhiều provenance records.
- Chốt source revision/checksum để phát hiện thay đổi và tự tạo version/reconcile chunks + Qdrant.
- Migration 051 chưa triển khai; schema 051 phải được review dựa trên toàn bộ knowledge contracts trước khi code.

## 2026-09-21 — Changelog continuation rule locked
- Khi changelog hiện tại quá lớn sẽ tạo file số kế tiếp.
- CHANGELOG.md → CHANGELOG_02.md → CHANGELOG_03.md → CHANGELOG_04.md...
- Không xóa hoặc viết lại lịch sử trong changelog cũ.
- Mỗi changelog mới phải ghi rõ vai trò continuation.
- Các thay đổi mới phải ghi ngày/giờ và liên kết tới file được thêm/thay đổi khi phù hợp.