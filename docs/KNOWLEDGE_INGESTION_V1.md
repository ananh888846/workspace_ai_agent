# Workspace AI Agent — KNOWLEDGE INGESTION V1

> Status: Design locked → Migration 051 baseline verified → Runtime integration ready — 2026-09-21

Đây là contract cho pipeline đưa dữ liệu bên ngoài vào Knowledge Systematization Agent. V1 triển khai Google Drive trước; Gmail, Facebook/Meta, Instagram, TikTok, Zalo, file upload và public URL dùng cùng contract khi provider capability/authorization được mở.

## 1. Mục tiêu
Knowledge Ingestion không phải Agent Core. Nó là pipeline nền để biến dữ liệu nguồn thành knowledge có version, provenance, asset storage, authorization context và vector index.
~~~text
Provider → Connector/Event → Authorization → Fetch → Normalize
→ Resolve Source + Asset → Identity → Version/Checksum
→ Store Asset + SQL metadata → Chunk → Embedding → Qdrant
~~~

## 2. Nguyên tắc bắt buộc
1. SQL là source of truth cho identity, ownership, tenant, provenance và authorization.
2. File Storage là nơi giữ binary; PostgreSQL giữ metadata/reference.
3. Qdrant chỉ là retrieval index, không phải authorization source.
4. Webhook/event endpoint không chạy full ingestion.
5. Credential chỉ được resolve sau Authorization ALLOW.
6. Một user có thể có nhiều external accounts; account phải được xác định bằng user_accounts.id.
7. Ingestion phải idempotent.
8. Thay đổi nguồn phải tạo/reconcile version, không ghi đè mù version cũ.
9. Provider-specific API logic không nằm trong Agent Core.
10. Delete/disable từ nguồn phải có reconciliation policy.
11. Background job phải giữ organization_id và actor/account context cần thiết để audit.
12. Storage backend phải có abstraction để sau này chuyển Local → NAS mà không đổi domain/application contract.

## 3. Ingestion lifecycle
RECEIVED → AUTHORIZED → FETCHING → NORMALIZING → SOURCE/ASSET RESOLUTION → VERSIONING → PERSISTING → CHUNKING → EMBEDDING → INDEXING → COMPLETED

Failure states: FAILED_RETRYABLE, FAILED_PERMANENT, SKIPPED_UNCHANGED, SKIPPED_UNAUTHORIZED.

## 4. Document identity
Identity ổn định theo organization_id + resource_id + provider + external_id. Tên file/title chỉ là metadata.

## 5. Source URL và provenance
Pipeline phải giữ URL nguồn ban đầu, canonical URL nếu resolve được, provider/account/resource, external ID, source revision và source checksum.
Một knowledge document/version có thể có nhiều provenance records nếu là derived/aggregated knowledge.

## 6. Version identity
Revision hoặc checksum không đổi → SKIPPED_UNCHANGED.
Content thay đổi → new document version → new/reconciled chunks → new embeddings → reconcile old Qdrant points.

## 7. Asset và file storage
Video, image, document và audio được lưu dưới StorageService.
~~~text
videos/<provider>/<external_id>/original.mp4
images/<provider>/<external_id>/original.jpg
documents/<provider>/<external_id>/original.pdf
audio/<provider>/<external_id>/original.mp3
~~~
PostgreSQL lưu asset metadata và storage_key, không lưu binary. Một document version có thể có nhiều asset.

## 8. Normalize contract
Normalizer tạo canonical document/source item gồm title, content, mime_type, source_url, canonical_url nếu có, author, published_at, updated_at, source_external_id, source_revision, metadata không chứa secret và asset references.
Image/video/document có thể cần extractor trước khi text được chunk/embed.

## 9. Chunk contract
Chunk phải có document/version reference, thứ tự ổn định, text canonical, character/token boundaries, content checksum, metadata retrieval và Qdrant point identity.

## 10. Embedding contract
Embedding worker nhận canonical chunk và model configuration. Model dimension phải đồng nhất với Qdrant collection tương ứng.

## 11. Authorization boundary
~~~text
Authentication → Organization Context → Account Resolver
→ Authorization → Credential Resolver → Provider API
~~~
Nếu DENY: CredentialResolver không được gọi và Provider API không được gọi.

## 12. Event / worker boundary
Webhook/provider notification chỉ xác minh, xác định context, ghi nhận event/job, enqueue worker và trả response nhanh.
Worker mới thực hiện fetch → normalize → asset → version → chunk → embed → index.

## 13. Provider rollout V1
Google là provider đầu tiên; Google Drive là source đầu tiên. Facebook/Meta, TikTok và Instagram chỉ ingest dữ liệu mà official API/integration cấp quyền hợp lệ.

## 14. Out of scope V1
Agent tự đăng bài; tự gửi tin nhắn; tự động thay đổi dữ liệu nguồn; scraping trái policy; cross-organization retrieval; dùng Qdrant làm permission store; đưa credential vào prompt/vector payload; phụ thuộc absolute local path trong domain/application.

## 15. Acceptance gate
Source/provenance contract, storage/asset contract và pipeline contract phải được chốt; DB gap review hoàn tất; Google Drive happy path; unchanged idempotent; changed source tạo version; source URL/canonical URL trace được; asset storage không phụ thuộc absolute local path; DENY không gọi provider; Qdrant failure retry/reconcile; audit đủ context và không chứa secret.