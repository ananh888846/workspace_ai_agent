# Workspace AI Agent — MIGRATION 051 SCHEMA REVIEW

> Ngày review: 2026-09-21
>
> Trạng thái: **SCHEMA REVIEW — READY FOR DESIGN LOCK**
>
> Phạm vi: Knowledge Source / Provenance / Document Version / Asset Storage / Chunk / Qdrant mapping.

## 1. Kết luận

Migration 051 cần được thiết kế như migration hậu V2.1 và không sửa ngược 001 → 050.

Schema hiện tại từ Migration 029–030 là nền tảng nhưng chưa đủ cho Knowledge Ingestion V1:

- `knowledge_documents` đang trộn document identity với source identity và version.
- Chưa có source/provenance entity riêng để lưu URL ban đầu, canonical URL, provider/account/resource/external ID và cho phép một knowledge item có nhiều nguồn.
- Chưa có document version entity phù hợp để giữ lịch sử nội dung khi source thay đổi.
- `knowledge_chunks` đang gắn trực tiếp với document, chưa gắn với một version cụ thể.
- Chưa có asset/storage metadata cho video, image, document, audio.
- Chưa có canonical content field để lưu nội dung đã normalize trong PostgreSQL.
- Qdrant point mapping hiện có nhưng chưa đủ context version/organization/provenance.

**Decision:** Migration 051 nên dùng mô hình `Source → Document → Version → Asset/Chunk`, với PostgreSQL là source of truth và File Storage là binary store.

## 2. Migration 029–030 hiện tại

### `knowledge_documents`

Hiện có:

- `resource_id`
- `title`
- `source_type`
- `source_id`
- `version`
- `checksum`
- `status`
- timestamps

Vấn đề:

1. `source_type/source_id` không đủ để biểu diễn provenance nhiều nguồn.
2. `version/checksum` đang nằm trên logical document nên khó giữ nhiều version có lifecycle rõ ràng.
3. Không có organization/account/provider/resource type/external ID đầy đủ.
4. Không có source URL/canonical URL.
5. Không có canonical content.

### `knowledge_chunks`

Hiện có document_id, chunk_index, content_hash, qdrant_point_id và token_count.

Vấn đề chính: chunk phải thuộc **document version**, không chỉ logical document. Nếu source thay đổi, version mới cần chunk mới/reconciled chunk mà không làm mất lịch sử version cũ.

## 3. Mô hình Migration 051 đề xuất

~~~text
knowledge_sources
        │
        ├── source identity + provenance
        │
        ▼
knowledge_documents
        │
        ▼
knowledge_document_versions
        │
        ├── knowledge_document_version_sources
        │
        ├── knowledge_assets
        │
        └── knowledge_chunks
                         │
                         ▼
                       Qdrant
~~~

## 4. Bảng A — `knowledge_sources`

Mục đích: stable source identity và provenance.

Đề xuất fields:

| Field | Type | Required | Ghi chú |
|---|---|---:|---|
| id | UUID | YES | PK |
| organization_id | UUID | YES | tenant boundary |
| user_account_id | UUID | YES/NULL theo provider | account context |
| resource_id | UUID | YES/NULL | resource đã resolve |
| provider | VARCHAR(64) | YES | google_drive/facebook/... |
| resource_type | VARCHAR(100) | YES | file/reel/post/... |
| external_id | VARCHAR(255) | YES | provider identity |
| source_url | TEXT | NO | URL phát hiện ban đầu |
| canonical_url | TEXT | NO | URL chuẩn sau resolve |
| source_revision | VARCHAR(255) | NO | provider revision nếu có |
| current_checksum | VARCHAR(255) | NO | checksum canonical current state |
| status | VARCHAR(32) | YES | active/deleted/unavailable |
| metadata | JSONB | YES | provider metadata, không secret |
| last_checked_at | TIMESTAMPTZ | NO | lần kiểm tra nguồn gần nhất |
| last_changed_at | TIMESTAMPTZ | NO | lần phát hiện thay đổi |
| created_at | TIMESTAMPTZ | YES | |
| updated_at | TIMESTAMPTZ | YES | |

Identity không dùng URL. Candidate unique key: `(organization_id, user_account_id, provider, resource_type, external_id)` với policy rõ cho source không gắn account.

## 5. Bảng B — `knowledge_documents`

Đây là **logical knowledge document**, không còn là nơi giữ version identity.

Đề xuất giữ/chuẩn hóa:

- id
- resource_id
- title
- status
- created_at
- updated_at

Không tiếp tục dùng `source_type`, `source_id`, `version`, `checksum` làm canonical version state sau khi 051 lock.

Để backward compatibility, Migration 051 cần có kế hoạch backfill từ schema 029 trước khi bỏ/đổi các cột cũ.

## 6. Bảng C — `knowledge_document_versions`

Đây là snapshot canonical của nội dung tại một thời điểm.

Đề xuất fields:

| Field | Type | Required | Ghi chú |
|---|---|---:|---|
| id | UUID | YES | PK |
| knowledge_document_id | UUID | YES | FK |
| version_no | INTEGER/BIGINT | YES | tăng dần theo document |
| source_revision | VARCHAR(255) | NO | revision provider |
| checksum | VARCHAR(255) | YES | checksum canonical content |
| canonical_content | TEXT | YES | nội dung normalize lưu trong PostgreSQL |
| content_type | VARCHAR(100) | YES | text/markdown/... |
| status | VARCHAR(32) | YES | active/superseded/deleted |
| metadata | JSONB | YES | parser/extractor metadata |
| created_at | TIMESTAMPTZ | YES | |

Unique nên có:

`UNIQUE(knowledge_document_id, version_no)`

và idempotency/revision policy theo checksum/source revision.

**Đây là nơi lưu nội dung canonical mà Agent sẽ dùng để tái dựng/chunk lại mà không phải gọi provider lần nữa.**

## 7. Bảng D — `knowledge_document_version_sources`

Mục đích: provenance mapping. Một version có thể có nhiều source.

Đề xuất:

| Field | Type | Required |
|---|---|---:|
| document_version_id | UUID | YES |
| source_id | UUID | YES |
| relation_type | VARCHAR(32) | YES | primary/derived/supporting |
| source_revision | VARCHAR(255) | NO | snapshot revision used |
| source_checksum | VARCHAR(255) | NO | snapshot checksum used |
| created_at | TIMESTAMPTZ | YES |

PK hoặc UNIQUE: `(document_version_id, source_id)`.

Điều này giải quyết trường hợp:

`Google + Facebook + TikTok → một derived knowledge document`.

## 8. Bảng E — `knowledge_assets`

Mục đích: metadata/reference của binary lớn.

| Field | Type | Required |
|---|---|---:|
| id | UUID | YES | PK |
| document_version_id | UUID | YES | FK |
| asset_type | VARCHAR(32) | YES | video/image/document/audio/thumbnail |
| file_name | VARCHAR(500) | NO | |
| mime_type | VARCHAR(255) | YES | |
| file_size | BIGINT | YES | bytes |
| checksum | VARCHAR(255) | YES | file checksum |
| storage_backend | VARCHAR(32) | YES | local/nas/... |
| storage_key | TEXT | YES | logical key, không absolute path |
| width | INTEGER | NO | image/video |
| height | INTEGER | NO | image/video |
| duration_ms | BIGINT | NO | video/audio |
| metadata | JSONB | YES | extractor metadata |
| created_at | TIMESTAMPTZ | YES | |

Không lưu binary trong PostgreSQL.

## 9. Bảng F — `knowledge_chunks`

Migration 051 phải đổi quan hệ chunk từ logical document sang document version.

Đề xuất tối thiểu:

- `id`
- `document_version_id`
- `chunk_index`
- `content` hoặc `content_hash` + content storage policy
- `content_hash`
- `qdrant_point_id`
- `token_count`
- timestamps

Khuyến nghị V1 lưu `content TEXT` trong SQL. Qdrant chỉ là index; không phụ thuộc Qdrant để tái dựng canonical knowledge.

Unique:

- `(document_version_id, chunk_index)`
- `qdrant_point_id`

## 10. Qdrant mapping

Qdrant payload nên đủ để pre-filter/reconcile nhưng không phải authorization source:

~~~text
organization_id
resource_id
knowledge_document_id
knowledge_document_version_id
knowledge_chunk_id
provider
user_account_id
checksum
~~~

Authorization vẫn phải resolve bằng PostgreSQL.

## 11. Foreign-key / tenant integrity

Migration 051 phải tuân Database V2.1:

- tenant-scoped knowledge tables phải có `organization_id` hoặc được chứng minh tenant qua resource/account bằng composite FK/constraint phù hợp;
- `resource_id` nếu có phải cùng organization;
- `user_account_id` nếu có phải thuộc đúng user/account context;
- không cho provenance cross-organization;
- derived document không được nối source thuộc tenant khác;
- `ON DELETE RESTRICT` cho lịch sử knowledge; reconciliation dùng status/tombstone thay vì cascade xóa mù.

## 12. Idempotency

Unchanged source:

~~~text
same identity + same revision/checksum
→ SKIPPED_UNCHANGED
~~~

Changed source:

~~~text
same source identity
→ new document_version
→ new/reconciled chunks
→ new Qdrant points
→ stale point reconciliation
~~~

Không tạo duplicate version khi worker retry.

## 13. Storage/NAS compatibility

Database chỉ lưu `storage_backend + storage_key`.

Không lưu absolute path kiểu:

`C:\Users\...` hoặc `/app/storage/...`.

StorageService quyết định cách resolve key.

V1: LocalStorage.
Future: NASStorage.

## 14. Migration/backfill strategy

Không sửa 029/030.

Migration 051 cần:

1. Tạo bảng mới.
2. Backfill logical document từ `knowledge_documents` hiện tại.
3. Tạo version ban đầu từ `version/checksum` hiện có.
4. Nếu nội dung cũ không tồn tại trong SQL, đánh dấu version là cần re-fetch/rebuild thay vì bịa nội dung.
5. Backfill chunk từ `knowledge_chunks` sang version mới nếu mapping xác định được.
6. Tạo source/provenance records từ resource/source fields khi đủ dữ liệu.
7. Sau khi verification PASS mới bỏ/deprecate columns cũ.

## 15. Các điểm chưa nên code nếu chưa quyết định

### A — Content size policy
PostgreSQL `TEXT` có thể chứa nội dung lớn, nhưng cần policy cho binary/extracted content cực lớn. Binary không lưu SQL.

### B — Source không có resource
Ví dụ một URL public được import trước khi provider resource được tạo. Schema phải cho phép source tạm thời chưa có resource nhưng vẫn giữ identity/provider/external_id.

### C — Derived knowledge
Cần phân biệt source document/version và derived/aggregated knowledge. Không overload `source_url` thành một nguồn duy nhất.

### D — Retention
Version cũ và binary cũ giữ bao lâu phải là policy riêng, không hard-code xóa cascade trong 051.

## 16. Review verdict

**Migration 051 chưa nên viết SQL production ngay tại thời điểm review này.**

Schema direction đã đủ rõ để chuyển sang **Schema Design Lock**, với 6 lớp chính:

1. `knowledge_sources`
2. `knowledge_documents`
3. `knowledge_document_versions`
4. `knowledge_document_version_sources`
5. `knowledge_assets`
6. `knowledge_chunks` gắn version

Sau khi chốt 4 policy còn mở ở mục 15, có thể viết Migration 051 và acceptance tests.

## 17. Multi-source Design Lock — 2026-09-21

### Nguyên tắc bắt buộc

Knowledge V1 phải **provider-neutral và multi-source**. Google Drive chỉ là provider đầu tiên triển khai, không phải kiến trúc trung tâm. Schema phải dùng được cho Facebook/Meta, Instagram, TikTok, Gmail, Zalo, file upload, public URL và provider tương lai mà không cần tạo bảng knowledge riêng cho từng provider.

Luồng chuẩn:

`Provider Adapter → Normalize → knowledge_sources → knowledge_documents → knowledge_document_versions → assets/chunks → Qdrant`

### Bốn policy đã chốt

**A. Content:** canonical normalized text và chunk content lưu PostgreSQL `TEXT` trong V1. Binary video/image/document/audio không lưu PostgreSQL; chỉ lưu metadata + `storage_backend/storage_key`.

**B. Source chưa có resource:** cho phép `resource_id = NULL` với status `unresolved`. Không được dùng trạng thái này để bypass authorization. Khi resolve được resource thì cập nhật resource reference nhưng giữ nguyên provenance.

**C. Derived knowledge:** hỗ trợ first-class. Một document version có thể có nhiều source thông qua `knowledge_document_version_sources`, với `relation_type = primary | derived | supporting`. Ví dụ Google + Facebook + TikTok có thể cùng đóng góp cho một derived knowledge version.

**D. Retention:** giữ version lịch sử và asset metadata; version cũ chuyển `superseded`; Migration 051 không hard-delete bằng cascade. Physical cleanup để retention worker/policy xử lý về sau.

### Multi-source acceptance cases

Migration 051 phải biểu diễn được tối thiểu: Google Drive, Facebook/Meta, Instagram, TikTok, Gmail, Zalo/provider tương lai; nhiều account trên cùng provider; source URL và canonical URL; một document version có nhiều source; source không đổi → `SKIPPED_UNCHANGED`; source thay đổi → version/chunk/Qdrant reconciliation; source delete/revoke → tombstone/status mà không phá lịch sử.

**Design Lock:** APPROVED.

Bước tiếp theo: production SQL Migration 051 + acceptance tests + PostgreSQL verification.
