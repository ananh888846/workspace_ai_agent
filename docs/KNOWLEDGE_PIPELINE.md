# Workspace AI Agent — KNOWLEDGE PIPELINE V1

> **Status:** Design locked — 2026-09-21
>
> Pipeline runtime contract cho Knowledge Systematization Agent.

## 1. Pipeline tổng thể

```text
Provider Notification / Scheduled Sync / Manual Import
                         ↓
                  Ingestion Job
                         ↓
               Authorization Gate
                         ↓
                    Fetcher
                         ↓
                   Normalizer
                         ↓
              Identity + Checksum
                         ↓
                 Version Resolver
                         ↓
                     Chunker
                         ↓
                   Embed Worker
                         ↓
              ┌──────────┴──────────┐
              ↓                     ↓
       PostgreSQL metadata       Qdrant
              ↓                     ↓
              └──────────┬──────────┘
                         ↓
                 Retrieval Service
                         ↓
                 Knowledge Agent
```

## 2. Job model

Mỗi ingestion request là một job có:

- `job_id`;
- `organization_id`;
- `user_account_id` nếu account-backed;
- `resource_id` nếu đã resolve;
- provider;
- external object ID;
- requested operation;
- attempt count;
- timestamps;
- status;
- error category nếu failure.

Job phải có correlation/request ID để trace qua worker, audit và provider call.

## 3. Stage 1 — Authorization

Trước fetch:

```text
Authentication
 → OrganizationContext
 → AccountResolver
 → AuthorizationService
 → CredentialResolver
```

Không được fetch external content trước khi authorization ALLOW.

## 4. Stage 2 — Fetch

Fetcher dùng credential context ngắn hạn.

Fetcher không ghi credential vào job payload, database metadata, logs hoặc Qdrant.

Fetch phải hỗ trợ pagination nếu provider API yêu cầu.

Rate limit phải chuyển thành retryable failure với backoff.

## 5. Stage 3 — Normalize

Normalizer chuyển provider response thành `KnowledgeSourceItem` theo `KNOWLEDGE_SOURCE_CONTRACT.md`.

Normalizer phải deterministic và không thực hiện authorization decision.

## 6. Stage 4 — Identity + checksum

Resolver xác định:

```text
organization_id
user_account_id
provider
resource_type
external_id
```

Sau đó tính/check `source_checksum`.

Nếu unchanged:

```text
SKIPPED_UNCHANGED
```

Không tạo version/chunks/vector mới.

## 7. Stage 5 — Version

Nếu changed:

```text
old version
     ↓
new version
     ↓
new chunks
     ↓
new embeddings
```

Version cũ không bị xóa tùy tiện. Retention/reconciliation phải là policy riêng.

## 8. Stage 6 — Chunk

Chunker nhận canonical content.

Yêu cầu:

- deterministic;
- giữ thứ tự;
- có stable chunk checksum;
- giữ document/version reference;
- metadata tối thiểu để trace về source.

Không chunk trực tiếp provider payload chưa normalize.

## 9. Stage 7 — Embedding

Embed worker nhận chunk text + embedding model/version.

Model dimension phải đồng nhất với Qdrant collection tương ứng.

V1 mặc định tách model configuration khỏi Agent Core để có thể đổi model mà không đổi provider contract.

## 10. Stage 8 — PostgreSQL

PostgreSQL lưu metadata/identity/authorization relationships và mapping tới vector index.

SQL không lưu vector đầy đủ nếu Qdrant là vector store chính, trừ khi sau này có quyết định mới.

## 11. Stage 9 — Qdrant

Qdrant lưu vector + payload retrieval tối thiểu.

Payload nên có stable identifiers như:

```text
organization_id
resource_id
knowledge_document_id
knowledge_chunk_id
version_id
provider
```

Không đưa secret vào payload.

Qdrant filter phải mang tenant/authorization constraints phù hợp.

## 12. Stage 10 — Reconciliation

Sau khi SQL và Qdrant hoàn tất, worker đánh dấu job `COMPLETED`.

Nếu SQL thành công nhưng Qdrant thất bại:

```text
job = retryable
Qdrant = pending/reconcile
```

Không tạo duplicate point khi retry.

Nếu Qdrant thành công nhưng final SQL commit thất bại, reconciliation job phải phát hiện orphan point và xử lý theo stable point identity.

## 13. Retrieval pipeline

```text
User Request
 ↓
Authentication
 ↓
Organization Context
 ↓
Capability / Authorization
 ↓
Knowledge Query
 ↓
Authorized Qdrant Filter
 ↓
Top-K chunks
 ↓
SQL metadata/source resolution
 ↓
Answer / Summary
```

Không trả kết quả chỉ dựa trên raw Qdrant payload nếu cần source/authorization verification.

## 14. Idempotency

Idempotency key có thể dựa trên:

```text
organization_id
+ user_account_id
+ provider
+ external_id
+ source_revision/checksum
```

Cùng key không tạo duplicate version ngoài policy.

## 15. Retry policy

Retryable:

- timeout;
- network failure;
- provider 429/rate limit;
- temporary 5xx;
- Qdrant unavailable.

Permanent:

- invalid source;
- unsupported content type;
- authorization denied;
- account revoked;
- malformed canonical data.

Retry phải có giới hạn và dead-letter/error state để tránh loop vô hạn.

## 16. Observability

Mỗi stage phải trace được:

```text
request_id
job_id
organization_id
user_id
account_id
resource_id
provider
stage
status
started_at
finished_at
error_code
```

Không log token, password, cookie, API key hoặc raw credential.

## 17. First implementation gate

Implementation đầu tiên chỉ cần Google Drive:

```text
Google Drive file
 ↓
Fetch
 ↓
Normalize
 ↓
Resource mapping
 ↓
Knowledge document/version
 ↓
Chunk
 ↓
Embedding
 ↓
Qdrant
 ↓
Authorized search
 ↓
Knowledge Agent answer
```

Chưa mở Facebook/TikTok/Instagram runtime cho đến khi Google happy path và contract tests PASS.
