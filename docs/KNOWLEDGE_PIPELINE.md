# Workspace AI Agent — KNOWLEDGE PIPELINE V1

> Status: Design locked — 2026-09-21

Pipeline runtime contract cho Knowledge Systematization Agent.

## 1. Pipeline tổng thể
~~~text
Provider Notification / Scheduled Sync / Manual Import
 ↓ Ingestion Job
 ↓ Authorization Gate
 ↓ Fetcher
 ↓ Normalizer
 ↓ Source + Asset Resolver
 ↓ Identity + Checksum
 ↓ Version Resolver
 ↓ PostgreSQL + File Storage
 ↓ Chunker
 ↓ Embed Worker
 ↓ Qdrant
 ↓ Retrieval Service
 ↓ Knowledge Agent
~~~

## 2. Job model
Job có job_id, organization_id, user_account_id nếu account-backed, resource_id nếu đã resolve, provider, external object ID, requested operation, attempt count, timestamps, status và error category.
Job phải có correlation/request ID.

## 3. Stage 1 — Authorization
Authentication → OrganizationContext → AccountResolver → AuthorizationService → CredentialResolver.
Không fetch external content trước khi authorization ALLOW.

## 4. Stage 2 — Fetch
Fetcher dùng credential context ngắn hạn, không ghi credential vào job payload, database metadata, logs hoặc Qdrant. Hỗ trợ pagination và retry rate limit.

## 5. Stage 3 — Normalize
Normalizer chuyển provider response thành KnowledgeSourceItem theo KNOWLEDGE_SOURCE_CONTRACT.md. Deterministic và không thực hiện authorization decision.

## 6. Stage 4 — Source + Asset Resolution
Resolver giữ source_url, canonical_url nếu có, provider, external_id, resource_id, asset_type, storage_backend và storage_key.
Tool có thể nhận share URL như https://www.facebook.com/share/r/18EZRZymHJ/ và resolve canonical resource URL/external ID nếu provider capability cho phép.
URL chỉ là provenance metadata; không thay thế identity.
Binary được lưu qua StorageService. PostgreSQL chỉ lưu metadata/reference.

## 7. Stage 5 — Identity + checksum
Resolver xác định organization_id, user_account_id, provider, resource_type, external_id rồi tính/check source_checksum.
Unchanged → SKIPPED_UNCHANGED và không tạo version/chunks/vector mới.

## 8. Stage 6 — Version
Changed → old version → new version → new/reconciled chunks → new embeddings. Version cũ không bị xóa tùy tiện.

## 9. Stage 7 — Persistence
PostgreSQL lưu source/provenance, document/version, asset metadata, storage reference, checksum/revision, authorization relationships và Qdrant point mapping.
File Storage giữ binary gốc/derived assets. Storage backend phải qua abstraction để LocalStorage có thể đổi sang NASStorage.

## 10. Stage 8 — Chunk
Chunker deterministic, giữ thứ tự, stable chunk checksum, document/version reference và metadata trace về source. Không chunk provider payload chưa normalize.

## 11. Stage 9 — Embedding
Embed worker nhận chunk text + embedding model/version. Dimension phải đồng nhất với Qdrant collection.

## 12. Stage 10 — Qdrant
Qdrant lưu vector + payload retrieval tối thiểu gồm organization_id, resource_id, knowledge_document_id, knowledge_chunk_id, version_id và provider.
Không đưa secret vào payload. Qdrant filter phải mang tenant/authorization constraints.

## 13. Stage 11 — Reconciliation
SQL thành công nhưng Qdrant thất bại → job retryable, Qdrant pending/reconcile.
Qdrant thành công nhưng final SQL commit thất bại → reconciliation phát hiện orphan point theo stable point identity.

## 14. Retrieval pipeline
User Request → Authentication → Organization Context → Capability/Authorization → Knowledge Query → Authorized Qdrant Filter → Top-K chunks → SQL metadata/source resolution → Asset/source trace khi cần → Answer/Summary.

## 15. Idempotency
Idempotency key có thể dựa trên organization_id + user_account_id + provider + external_id + source_revision/checksum.

## 16. Retry policy
Retryable: timeout, network failure, provider 429, temporary 5xx, Qdrant unavailable.
Permanent: invalid source, unsupported content type, authorization denied, account revoked, malformed canonical data.

## 17. Observability
Trace request_id, job_id, organization_id, user_id, account_id, resource_id, provider, stage, status, timestamps và error_code. Không log credential.

## 18. Migration 051 runtime gate

Migration 051 PostgreSQL verification và acceptance AT-051-01..11 đã PASS. DB schema gate đã đóng. Bước kế tiếp là runtime integration cho Google Drive happy path.

## 19. First implementation gate
Google Drive file → Fetch → Normalize → Source/Asset resolution → Knowledge document/version → File Storage → Chunk → Embedding → Qdrant → Authorized search → Knowledge Agent answer.
Chưa mở Facebook/TikTok/Instagram runtime cho đến khi Google happy path và contract tests PASS.