# Workspace AI Agent — KNOWLEDGE STORAGE & PROVENANCE V1

> Status: Design locked — 2026-09-21
>
> Thiết kế lưu trữ binary asset, provenance và source version cho Knowledge Systematization Agent. Đây là contract nền đã được hiện thực hóa bởi Migration 051.

## 1. Mục tiêu

Knowledge không chỉ là text. Một source có thể có text/document, image, video, audio và nội dung được trích xuất từ binary.

V1 phải lưu được nguồn gốc + nội dung + file asset + lịch sử thay đổi, nhưng không biến PostgreSQL thành binary storage.

## 2. Ba lớp lưu trữ

~~~text
PostgreSQL
├── identity
├── provenance
├── document/version
├── asset metadata
├── checksum
└── storage reference

File Storage
├── videos/
├── images/
├── documents/
└── audio/

Qdrant
└── embeddings + retrieval metadata
~~~

PostgreSQL là source of truth. File Storage giữ binary. Qdrant chỉ là retrieval/index layer.

## 3. Source và provenance

Mỗi source item phải trace được tối thiểu: organization_id, user_account_id, provider, resource_id, resource_type, external_id, source_url, canonical_url nếu có, source_revision nếu có và source_checksum.

source_url là URL ban đầu được phát hiện/import.

canonical_url là URL chuẩn sau khi tool/provider resolver xử lý redirect hoặc share URL.

Ví dụ:

~~~text
source_url:
https://www.facebook.com/share/r/18EZRZymHJ/

canonical_url:
https://www.facebook.com/reel/<resolved-id>
~~~

Không dùng URL làm identity duy nhất. Identity vẫn dựa trên tenant + account + provider + resource type + external ID.

## 4. Source snapshot/version

Mỗi lần source được kiểm tra có snapshot/version với fetched_at, source_revision nếu có, source_checksum, content reference và metadata.

Không đổi revision/checksum → SKIPPED_UNCHANGED.

Thay đổi revision/checksum → tạo version mới, reconcile chunks, embedding và Qdrant.

Version cũ không bị ghi đè mù; retention là policy riêng.

## 5. Asset storage

Binary asset không lưu trực tiếp trong PostgreSQL.

Logical storage key:

~~~text
videos/<provider>/<external_id>/original.mp4
images/<provider>/<external_id>/original.jpg
documents/<provider>/<external_id>/original.pdf
audio/<provider>/<external_id>/original.mp3
~~~

Database lưu asset_id, document_version_id, asset_type, mime_type, file_name, file_size, checksum, storage_backend, storage_key và created_at.

## 6. Storage abstraction

~~~text
StorageService
├── LocalStorage   ← V1
└── NASStorage     ← future
~~~

Application/ingestion chỉ làm việc với StorageService. Không hard-code absolute local path trong domain/application.

## 7. Binary processing

Image: asset → Vision/OCR → extracted description/text → Knowledge content → chunk/embed.

Video: asset → thumbnail/frame extraction → transcript nếu capability cho phép → visual/text metadata → Knowledge content → chunk/embed.

Document: asset → parser/OCR nếu cần → canonical text → chunk/embed.

Binary gốc vẫn được giữ theo retention/storage policy.

## 8. Một document có thể có nhiều asset

Ví dụ một Facebook Reel có Source, Video Asset, Image Asset, Transcript/Text và Knowledge Chunks.

Không tạo provider-specific knowledge tables như facebook_videos hay tiktok_posts.

## 9. Derived / aggregated knowledge

Một knowledge item có thể được tạo từ nhiều nguồn. Provenance phải giữ được quan hệ ngược về từng source/version.

~~~text
Source A ─┐
Source B ─┼→ Derived Knowledge
Source C ─┘
~~~

Không gộp nhiều nguồn thành một URL hoặc một source_id duy nhất.

## 10. Security

Không lưu access token, refresh token, API key, cookie/session secret hoặc private credential trong asset metadata, source metadata, Qdrant payload hoặc logs.

File access phải đi qua authorization context phù hợp.

## 11. Migration 051 scope

Migration 051 phải giải quyết tối thiểu: source/provenance; source URL + canonical URL; document/version; source revision/checksum; asset metadata + storage reference; document-version ↔ asset; document/version ↔ source provenance; unique/index cho idempotency và reconciliation.

Migration 051 đã được triển khai và runtime verification/acceptance đã PASS. Contract này là baseline cho ingestion runtime.