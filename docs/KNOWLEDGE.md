# Workspace AI Agent — KNOWLEDGE V1 / V2.1

## 1. Mục tiêu
Knowledge Systematization Agent là capability đầu tiên. V1 triển khai Google Drive trước; kiến trúc provider-neutral để mở rộng Gmail, Facebook/Meta, Instagram, TikTok, Zalo, file upload, public URL và provider tương lai khi capability/authorization được phê duyệt.
Knowledge không chỉ là text. Hệ thống quản lý source, document/version, binary asset và vector index.

## 2. Pipeline
Source URL / Provider Event → Resolve Source + Resource → Fetch → Normalize → Store Asset → Document Version + Checksum → Chunk → Embedding → PostgreSQL + Qdrant → Authorized Retrieval.

## 3. SQL vs File Storage vs Qdrant
PostgreSQL giữ source/provenance, resource/account/ownership, document/version, checksum/revision, asset metadata, storage backend/key, package/access mapping và Qdrant point mapping.
File Storage giữ videos, images, documents, audio, thumbnails/derived files. V1 có thể dùng local storage; kiến trúc phải cho phép chuyển sang NAS.
Qdrant giữ embeddings và retrieval metadata tối thiểu. Qdrant không phải source of truth và không phải permission store.

## 4. Sources dự kiến
Google Drive; Gmail; Facebook/Meta; Instagram; TikTok; Zalo; file upload; public URL; device-generated documents/images và các provider tương lai.

## 5. Source URL và provenance
Giữ URL nguồn ban đầu và canonical URL nếu resolve được.
~~~text
source_url:
https://www.facebook.com/share/r/18EZRZymHJ/

canonical_url:
https://www.facebook.com/reel/<resolved-id>
~~~
URL chỉ là provenance metadata. Identity vẫn dựa trên tenant/account/provider/resource/external ID.
Một knowledge item có thể có nhiều provenance records nếu được tổng hợp từ nhiều nguồn.

## 6. Versioning
Revision/checksum không đổi → SKIPPED_UNCHANGED.
Thay đổi → new document version → new/reconciled chunks → new embeddings → Qdrant reconciliation.
Không ghi đè mù version cũ.

## 7. Binary processing
Image: lưu asset riêng, sau đó có thể chạy Vision/OCR để tạo canonical text/metadata.
Video: lưu asset riêng; nếu capability cho phép, tạo thumbnail, frame metadata và transcript.
Document: lưu asset riêng và parse/OCR thành canonical text trước chunk/embed.

## 8. Ingestion
Provider ingestion phải chuẩn hóa dữ liệu trước khi index. Ingestion không được tự mở quyền truy cập. Mọi fetch phải qua authorization context.

## 9. Search
Knowledge search phải chạy trong authorization context. Khi cần, Agent truy ngược SQL để trả provenance: provider, account, resource, URL, version và asset reference.

## 10. Contract documents
- KNOWLEDGE_SOURCE_CONTRACT.md
- KNOWLEDGE_INGESTION_V1.md
- KNOWLEDGE_PIPELINE.md
- KNOWLEDGE_STORAGE_PROVENANCE_V1.md

Migration 051 phải được review dựa trên toàn bộ các contract này trước khi implementation.

## 11. Migration 051 gate

Migration 051 đã được runtime verification trên PostgreSQL và acceptance AT-051-01..11 đã PASS. Schema Knowledge V1 hiện là baseline để triển khai ingestion runtime.
