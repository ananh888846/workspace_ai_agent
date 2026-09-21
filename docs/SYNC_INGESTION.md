# Workspace AI Agent — Sync / Ingestion V2.1

> Kiến trúc đồng bộ dữ liệu provider → Knowledge. Webhook không chạy full ingestion đồng bộ.

## 1. Mục tiêu

Thiết kế pipeline cho Google Drive trước, sau đó mở rộng cho Gmail/Meta/Zalo/Telegram/provider khác.

Mục tiêu:

- phát hiện file/resource mới hoặc thay đổi;
- xác minh webhook/event;
- ghi nhận sync event có idempotency;
- worker fetch dữ liệu từ provider;
- tạo document version;
- normalize/chunk/embed;
- cập nhật SQL metadata và Qdrant;
- không làm mất tenant/resource/account authorization context.

## 2. Luồng chuẩn

```text
Provider Webhook / Push
        ↓
Webhook Verification
        ↓
Sync Event / Idempotency
        ↓
Queue / Worker
        ↓
Provider Account + Credential Resolution
        ↓
Fetch Resource
        ↓
Normalize
        ↓
Document Version + Checksum
        ↓
Chunk
        ↓
Embedding
        ↓
SQL metadata
        ↓
Qdrant upsert
        ↓
Audit / Sync Result
```

Webhook HTTP request chỉ nên xác minh, parse và enqueue/record event. Không fetch toàn bộ file và không chạy embedding/Qdrant trong webhook request.

## 3. Authorization boundary

Worker không được coi webhook là authorization.

Trước khi fetch protected provider data:

1. xác định organization;
2. xác định user/account/resource;
3. resolve candidate account;
4. kiểm tra capability/account/resource/package policy khi package scope áp dụng;
5. chỉ sau ALLOW mới resolve credential và gọi provider.

Credential không đi qua message queue dưới dạng plaintext.

## 4. Idempotency

Mỗi provider event phải có identity ổn định khi provider hỗ trợ.

Tối thiểu cần:

- provider;
- external event/resource id;
- observed/change token nếu có;
- received_at;
- processing status;
- retry count;
- last_error;
- correlation/request id.

Một event có thể được delivery nhiều lần nhưng không được tạo duplicate document version hoặc duplicate Qdrant point ngoài policy.

## 5. Document versioning

Khi resource thay đổi:

```text
resource
 ↓
fetch
 ↓
checksum / version
 ↓
compare
 ├─ unchanged → no-op
 └─ changed
       ↓
   new knowledge document version
       ↓
   replace/reconcile chunks
       ↓
   Qdrant upsert/delete stale points
```

SQL là source of truth cho version/checksum/status.

## 6. Qdrant authorization payload

Payload tối thiểu cần thiết theo domain có thể gồm:

- organization_id;
- resource_id;
- owner_user_id;
- provider;
- user_account_id;
- package_version_id khi package-scoped;
- knowledge_document_id;
- knowledge_chunk_id;
- document_version/checksum.

Không coi Qdrant payload là nguồn cấp quyền. Authorization policy vẫn nằm ở application/SQL boundary.

## 7. Failure / retry

Worker phải phân biệt:

- webhook verification failure;
- authorization denied;
- account/credential unavailable;
- provider transient error;
- provider permanent error;
- normalization error;
- embedding error;
- Qdrant error.

Retry chỉ áp dụng cho lỗi transient/idempotent. Authorization denied không retry vô hạn.

## 8. Delete / revoke

Nếu provider báo resource deleted/revoked:

1. ghi sync event;
2. cập nhật resource/document status;
3. đánh dấu chunks stale hoặc deleted theo retention policy;
4. xóa/disable Qdrant points tương ứng;
5. ghi audit.

Không xóa audit history chỉ vì resource bị xóa ở provider.

## 9. Multi-account

Một user có thể có nhiều account cùng provider.

Nếu event/resource xác định được external account, sync phải bind chính xác vào `user_accounts.id`. Không để LLM chọn account cho background sync.

## 10. Phase boundary

Sync/Ingestion là Phase Knowledge. Không cần implement đầy đủ trước khi Core Authorization + Accounts + Resources ổn định.

## 11. Acceptance tests

- duplicate webhook không tạo duplicate version;
- event của Account A không ingest vào Account B;
- unauthorized resource không được retrieve/index ngoài policy;
- credential không được resolve khi authorization fail;
- provider error transient được retry có giới hạn;
- Qdrant point có payload đủ để pre-filter theo authorization context;
- changed file tạo version/chunks mới và reconcile stale points.
