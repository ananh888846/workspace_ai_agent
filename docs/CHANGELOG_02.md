# CHANGELOG_02.md

> Changelog continuation for `docs/CHANGELOG.md`.
>
> **Rule:** Khi một file CHANGELOG trở nên quá lớn, không tiếp tục phình file cũ. Tạo file kế tiếp theo thứ tự `CHANGELOG_02.md`, `CHANGELOG_03.md`, `CHANGELOG_04.md`... và tiếp tục ghi log theo thứ tự thời gian. File mới phải ghi rõ đây là continuation của file trước.

## 2026-09-21 — Knowledge Ingestion V1 contracts locked

- Thêm [`docs/KNOWLEDGE_INGESTION_V1.md`](./KNOWLEDGE_INGESTION_V1.md): lifecycle, authorization boundary, idempotency, versioning, retry và provider rollout.
- Thêm [`docs/KNOWLEDGE_SOURCE_CONTRACT.md`](./KNOWLEDGE_SOURCE_CONTRACT.md): canonical source item, identity, account/resource binding, checksum và provider mapping.
- Thêm [`docs/KNOWLEDGE_PIPELINE.md`](./KNOWLEDGE_PIPELINE.md): Fetch → Normalize → Version → Chunk → Embed → PostgreSQL/Qdrant → Retrieval.
- Chốt Google Drive là provider/source đầu tiên cho end-to-end implementation; Facebook/Meta, TikTok và Instagram chỉ mở sau khi Google gate PASS.
- Chưa thay đổi production schema và chưa viết Agent runtime code.

## 2026-09-21 — Changelog continuation rule locked

- Từ thời điểm này, khi changelog hiện tại quá lớn sẽ tạo file số kế tiếp thay vì tiếp tục mở rộng file cũ.
- Quy tắc đặt tên: `CHANGELOG.md` → `CHANGELOG_02.md` → `CHANGELOG_03.md` → `CHANGELOG_04.md`...
- Không xóa hoặc viết lại lịch sử trong các changelog cũ.
- Mỗi changelog mới phải có link tới file trước và ghi rõ vai trò continuation.
- Các thay đổi mới phải ghi ngày/giờ và liên kết Markdown trực tiếp tới file được thêm/thay đổi khi phù hợp.
