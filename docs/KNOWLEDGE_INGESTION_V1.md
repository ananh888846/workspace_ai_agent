# Workspace AI Agent — KNOWLEDGE INGESTION V1

> **Status:** Design locked — 2026-09-21
>
> Đây là contract cho pipeline đưa dữ liệu bên ngoài vào Knowledge Systematization Agent. V1 triển khai Google trước; Facebook/Meta, TikTok và Instagram dùng cùng contract khi provider capability được mở.

## 1. Mục tiêu

Knowledge Ingestion không phải Agent Core. Nó là pipeline nền để biến dữ liệu nguồn thành knowledge có version, metadata, authorization context và vector index.

```text
Provider
  ↓
Connector
  ↓
Ingestion Event
  ↓
Fetch
  ↓
Normalize
  ↓
Document Identity
  ↓
Version / Checksum
  ↓
Chunk
  ↓
Embedding
  ↓
PostgreSQL metadata + authorization
  ↓
Qdrant index
```

## 2. Nguyên tắc bắt buộc

1. **SQL là source of truth** cho identity, ownership, tenant và authorization.
2. **Qdrant chỉ là retrieval index**, không phải authorization source.
3. Webhook/event endpoint không chạy full ingestion.
4. Credential chỉ được resolve sau Authorization ALLOW.
5. Một user có thể có nhiều external accounts; account phải được xác định bằng `user_accounts.id`, không để LLM tự chọn secret/account.
6. Ingestion phải idempotent.
7. Thay đổi nguồn phải tạo/reconcile version, không ghi đè mù version cũ.
8. Provider-specific API logic không nằm trong Agent Core.
9. Delete/disable từ nguồn phải có reconciliation policy; không để vector cũ tồn tại vô thời hạn.
10. Mọi background job phải giữ `organization_id` và actor/account context cần thiết để audit.

## 3. Ingestion lifecycle

```text
RECEIVED
  ↓
AUTHORIZED
  ↓
FETCHING
  ↓
NORMALIZING
  ↓
VERSIONING
  ↓
CHUNKING
  ↓
EMBEDDING
  ↓
INDEXING
  ↓
COMPLETED
```

Failure states:

- `FAILED_RETRYABLE` — lỗi tạm thời/provider rate limit/network.
- `FAILED_PERMANENT` — dữ liệu không hợp lệ, authorization không còn hợp lệ hoặc provider trả lỗi không thể retry.
- `SKIPPED_UNCHANGED` — checksum/source revision không đổi.
- `SKIPPED_UNAUTHORIZED` — không được phép ingest resource/account.

Retry phải idempotent; không tạo duplicate document/version/chunk khi job được chạy lại.

## 4. Document identity

Một knowledge document phải có identity ổn định theo source/resource, không theo tên hiển thị.

```text
organization_id
resource_id
provider
external_id
```

Tên file/title chỉ là metadata.

`resource_id` liên kết resource đã được authorization model kiểm soát. Provider external ID không được dùng thay thế tenant boundary.

## 5. Version identity

Mỗi lần nội dung có thay đổi cần xác định version bằng source revision hoặc checksum nội dung chuẩn hóa.

```text
source revision unchanged
        → SKIPPED_UNCHANGED

content changed
        → new document version
        → new chunks
        → new embeddings
        → reconcile old Qdrant points
```

Nếu provider không có revision đáng tin cậy, dùng checksum của canonical normalized content.

## 6. Normalize contract

Normalizer chuyển provider payload thành canonical document:

- `title`
- `content`
- `mime_type`
- `source_url` nếu có
- `author` nếu có
- `published_at` nếu có
- `updated_at` nếu có
- `source_external_id`
- `source_revision` nếu có
- `metadata` không chứa secret

Không đưa OAuth token, API key, cookie, device secret hoặc credential material vào canonical content/metadata.

## 7. Chunk contract

Chunk phải có:

- document/version reference;
- thứ tự ổn định;
- text canonical;
- character/token boundaries;
- content checksum;
- metadata cần cho retrieval;
- Qdrant point identity.

Chunking phải deterministic với cùng canonical content và cùng chunking configuration.

## 8. Embedding contract

Embedding worker nhận canonical chunk và model configuration.

Model/dimension phải được ghi nhận ở index metadata hoặc mapping phù hợp. Không trộn vector khác dimension vào cùng collection.

Qdrant failure không được làm mất SQL metadata; job phải có khả năng retry/reconcile.

## 9. Authorization boundary

Trước provider fetch:

```text
Authentication
 → Organization Context
 → Account Resolver
 → Authorization
 → Credential Resolver
 → Provider API
```

Nếu DENY:

```text
CredentialResolver = NOT CALLED
Provider API = NOT CALLED
```

Retrieval cũng phải giữ authorization context tương ứng.

## 10. Event / worker boundary

Webhook hoặc provider notification chỉ:

1. xác minh request/signature nếu provider hỗ trợ;
2. xác định tenant/account/resource context;
3. ghi nhận event/job request;
4. enqueue worker;
5. trả response nhanh.

Worker mới thực hiện fetch → normalize → version → chunk → embed → index.

## 11. Provider rollout V1

### Google

Provider đầu tiên để test end-to-end. Google Drive là source đầu tiên.

### Facebook/Meta

Chỉ ingest dữ liệu mà official API/integration cấp quyền hợp lệ. Không đưa scraping vào core pipeline.

### TikTok

Adapter riêng, phụ thuộc capability/API được cấp.

### Instagram

Adapter riêng dù thuộc hệ sinh thái Meta; không giả định quyền của Facebook tự động áp dụng cho Instagram.

## 12. Out of scope V1

- Agent tự đăng bài.
- Agent tự gửi tin nhắn.
- Tự động thay đổi dữ liệu nguồn.
- Scraping trái với điều khoản/API policy.
- Cross-organization retrieval.
- Dùng Qdrant làm permission store.
- Đưa credential vào prompt hoặc vector payload.

## 13. Acceptance gate

Knowledge Ingestion V1 chỉ mở implementation khi:

- source contract được chốt;
- pipeline contract được chốt;
- DB gap review hoàn tất;
- Google Drive happy path chạy được;
- unchanged source là idempotent;
- changed source tạo version đúng;
- authorization DENY không gọi provider;
- Qdrant failure có retry/reconcile;
- audit có đủ context mà không chứa secret.
