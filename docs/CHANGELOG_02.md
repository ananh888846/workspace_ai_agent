# CHANGELOG_02.md

> Changelog continuation for docs/CHANGELOG.md.
>
> Rule: khi changelog hiện tại quá lớn, tạo file kế tiếp theo thứ tự CHANGELOG_03.md, CHANGELOG_04.md...

## 2026-09-21 — Knowledge Ingestion V1 contracts locked
- Thêm docs/KNOWLEDGE_INGESTION_V1.md.
- Thêm docs/KNOWLEDGE_SOURCE_CONTRACT.md.
- Thêm docs/KNOWLEDGE_PIPELINE.md.
- Chốt Google Drive là provider/source đầu tiên; Facebook/Meta, TikTok và Instagram chỉ mở sau Google gate PASS.

## 2026-09-21 — Knowledge storage/provenance architecture locked
- Thêm docs/KNOWLEDGE_STORAGE_PROVENANCE_V1.md.
- Chốt source URL + canonical URL là provenance metadata.
- Chốt canonical content/metadata/version trong PostgreSQL; binary trong File Storage.
- Chốt StorageService để LocalStorage có thể chuyển sang NASStorage.
- Chốt source revision/checksum để phát hiện thay đổi và reconcile version/chunk/Qdrant.
- Migration 051 chưa triển khai.

## 2026-09-21 — Migration 051 schema review
- Thêm docs/MIGRATION_051_SCHEMA_REVIEW.md.
- Review Migration 029–030 và Database V2.1 contracts.
- Xác định gap: source/provenance chưa first-class; document đang trộn identity/version; chunk chưa gắn version; chưa có asset/storage metadata; chưa có canonical content trong SQL.
- Đề xuất 6 lớp schema: knowledge_sources, knowledge_documents, knowledge_document_versions, knowledge_document_version_sources, knowledge_assets và knowledge_chunks gắn document version.
- Chốt PostgreSQL là source of truth, File Storage là binary store, Qdrant là retrieval/index layer.
- Chưa viết production SQL Migration 051 cho đến khi các policy còn mở được chốt.

## 2026-09-21 — Migration 051 Schema Design Lock
- Chốt Migration 051 theo kiến trúc provider-neutral và multi-source; Google Drive chỉ là provider đầu tiên.
- Xác nhận schema phải hỗ trợ Facebook/Meta, Instagram, TikTok, Gmail, Zalo, upload, public URL và provider tương lai.
- Chốt canonical text/chunk trong PostgreSQL; binary qua File Storage.
- Chốt source có thể tạm thời chưa có resource; không được bypass authorization.
- Chốt derived knowledge hỗ trợ nhiều source qua `knowledge_document_version_sources`.
- Chốt retention giữ lịch sử version và không cascade hard-delete.
- Design Lock = APPROVED.

## 2026-09-21 — Production SQL Migration 051 implemented
- Thêm `migrations/051_knowledge_v1.sql`.
- Thêm `knowledge_sources` với source identity/provenance, source URL + canonical URL, account/resource context và tenant isolation.
- Thêm `knowledge_document_versions` để giữ canonical content/version/checksum.
- Thêm `knowledge_document_version_sources` cho primary/derived/supporting multi-source provenance.
- Thêm `knowledge_assets` cho metadata binary; binary không lưu trong PostgreSQL.
- Nâng `knowledge_chunks` từ logical document sang document version, vẫn giữ Qdrant point mapping.
- Có backfill từ 029/030; legacy version thiếu canonical content được đánh dấu `rebuild_required`, không bịa nội dung.
- Không sửa migration 001–050.

## 2026-09-21 — Migration 051 acceptance contract
- Thêm `database/tests/acceptance_051.sql`.
- Thêm `docs/MIGRATION_051_ACCEPTANCE.md`.
- Acceptance bao phủ six-layer schema, provider-neutral source, idempotency, cross-tenant rejection, version/checksum, provenance, asset storage key và version-scoped chunk.
- PostgreSQL runtime verification chưa được ghi PASS cho đến khi chạy thực tế.

## 2026-09-21 — Knowledge Ingestion V1 core implementation
- Thêm canonical `KnowledgeSourceItem` và `KnowledgeAssetRef` tại `app/domain/knowledge/`.
- Thêm application ingestion service với authorization gate, checksum idempotency, versioning, chunking, embedding và Qdrant reconciliation ports.
- Thêm provider-neutral `ProviderAdapter` contract.
- Thêm Google Drive normalizer đầu tiên; provider adapter chỉ normalize, không tự authorize/resolve credential.
- Thêm unit contract tests cho DENY, first ingestion và unchanged checksum.
- Cập nhật `docs/SOURCE_TREE_V2.md` để ghi nhận phase Knowledge Ingestion V1.
- Chưa gọi Google API/Qdrant runtime trong bước này; runtime integration sẽ thực hiện sau khi PostgreSQL Migration 051 verification PASS.


## 2026-09-21 — Migration 051 baseline audit + SQL correction
- Xác nhận PostgreSQL baseline 001–050 trên database sạch: **45 bảng**.
- Xác nhận `knowledge_documents` và `knowledge_chunks` hiện tại đến từ Migration 029/030.
- Xác nhận `idx_knowledge_chunks_content_hash` đã tồn tại từ Migration 030.
- Hoàn thiện/publish `database/migrations/051_knowledge_v1.sql` theo baseline thực tế.
- Migration 051 **không tạo lại** `idx_knowledge_chunks_content_hash`, loại bỏ nguyên nhân duplicate-index đã gặp trước đó.
- Cập nhật acceptance 051 để kiểm tra thực tế multi-source provenance.
- Runtime verification của Migration 051 vẫn **PENDING** cho đến khi chạy trên PostgreSQL thực tế.


## 2026-09-21 — Migration 051 PostgreSQL runtime verification PASS
- Reset PostgreSQL database và chạy lại migrations 001–050 thành công: **45 bảng baseline**.
- Áp dụng Migration 051 thành công.
- Chạy `database/tests/acceptance_051.sql`: **AT-051-01..11 PASS**.
- Acceptance kết thúc bằng `ROLLBACK`; test fixture không được giữ lại.
- Đóng Migration 051 DB Gate.
- Cập nhật các Knowledge contract/status docs để phản ánh runtime state thực tế.
- Bước tiếp theo: Knowledge Ingestion V1 runtime integration, bắt đầu với Google Drive happy path.
## 2026-09-21 — Docs synchronization check after Migration 051 PASS
- Kiểm tra lại các tài liệu Knowledge V1 trên GitHub sau khi Migration 051 và acceptance AT-051-01..11 đã PASS.
- Phát hiện `docs/KNOWLEDGE_INGESTION_V1.md` còn ghi trạng thái đầu tài liệu là `Design locked`, chưa phản ánh rõ DB gate đã đóng và runtime integration đã sẵn sàng.
- Đồng bộ trạng thái thành: Design locked → Migration 051 baseline verified → Runtime integration ready.
- Không thay đổi schema/migration 001–051.
## 2026-09-21 — Migration 051 final MD review + PASS closure
- Review/chốt các MD liên quan: `MIGRATION_051_SCHEMA_REVIEW.md`, `MIGRATION_051_ACCEPTANCE.md`, `KNOWLEDGE.md`, `KNOWLEDGE_INGESTION_V1.md`, `KNOWLEDGE_STORAGE_PROVENANCE_V1.md`, `KNOWLEDGE_SOURCE_CONTRACT.md`, `KNOWLEDGE_PIPELINE.md`.
- Kết quả: các tài liệu cùng phản ánh một trạng thái: Migration 051 đã **RUNTIME VERIFIED / PASS / GATE CLOSED**; Knowledge V1 schema là baseline cho ingestion runtime.
- Acceptance `AT-051-01..11`: **PASS** với transaction `ROLLBACK`.
- Đồng bộ trạng thái đầu tài liệu cho storage/provenance, source contract và pipeline để không còn mâu thuẫn với runtime gate đã đóng.
- Quyết định chốt: **không sửa migrations 001–050**; bước tiếp theo là Knowledge Ingestion V1 runtime integration, bắt đầu Google Drive happy path.


## 2026-09-21 — Google Calendar Event CRUD contract locked

- Thêm [docs/GOOGLE_CALENDAR.md](./GOOGLE_CALENDAR.md) làm contract cho Google Calendar Event CRUD.
- Chốt `calendar.read` cho đọc và `calendar.write` cho tạo/sửa/xóa.
- Chốt Google Calendar là account-backed capability, hỗ trợ multi-account và delegation qua authorization hiện có.
- Chốt update/delete phải xác định event mục tiêu; nhiều candidate không được tự chọn.
- Chốt không tạo Migration 052 chỉ cho Calendar Event CRUD; sử dụng resource/account/authorization/audit model V2.1 hiện tại.
- Bước tiếp theo: implementation provider adapter → tools → authorization → tests → runtime verification.


## 2026-09-21 — Google Calendar provider adapter V1 bắt đầu

- Thêm `app/providers/google/calendar/adapter.py`.
- Thêm `app/providers/google/calendar/__init__.py`.
- Adapter triển khai provider mapping cho `list_events`, `get_event`, `create_event`, `update_event`, `delete_event`.
- Adapter chỉ nhận Google Calendar service đã được inject; chưa tự resolve account, credential hoặc authorization.
- Thêm unit contract test `tests/unit/providers/test_google_calendar_adapter.py`.
- Chưa tạo Migration 052.
- Chưa tích hợp Google OAuth/API runtime; bước kế tiếp là nối CredentialResolver/AccountResolver và Google Calendar API client.


## 2026-09-21 — Google Calendar API client boundary

- Thêm `app/providers/google/calendar/client.py`.
- Client nhận credential context đã được authorize; không tự resolve account/permission/secret.
- Định nghĩa Calendar read/write OAuth scopes.
- Thêm unit contract test cho scope constants.
- Đồng bộ `docs/GOOGLE_CALENDAR.md` với credential boundary và runtime dependency.
- Chưa tạo Migration 052.


## 2026-09-21 — Google Calendar application/tool boundary

- Thêm `app/application/calendar.py` làm application orchestration boundary.
- Execution order được chốt: AccountResolver → AuthorizationService → CredentialResolver → ToolResolver → Tool.
- Nếu Authorization = DENY: CredentialResolver và ToolResolver không được gọi.
- Thêm `app/tools/calendar.py` cho `calendar.read` và `calendar.write` actions.
- Thêm unit test `tests/unit/application/test_calendar_application.py` cho DENY/ALLOW boundary.
- Cập nhật `docs/GOOGLE_CALENDAR.md`.
- Chưa tạo Migration 052; chưa tạo runtime AccountResolver/CredentialResolver giả.


## 2026-09-21 — Core authorization runtime boundary + local Calendar DB fixture

- Thêm `app/application/core_runtime.py` với AgentContext, AccountResolver, AuthorizationService và CredentialResolver contracts/runtime boundaries.
- Khóa nguyên tắc: CredentialResolver chỉ được resolve sau Authorization = ALLOW.
- Multi-account không tự đoán; nhiều candidate trả `account_selection_required`.
- Thêm `tests/unit/application/test_core_runtime.py` cho account selection và credential boundary.
- Thêm `scripts/calendar/bootstrap_test_data.sql` để tạo tenant/user/role/permission/Google account metadata cho local test.
- Fixture không chứa OAuth access/refresh token và không tạo credential giả.
- Cập nhật `docs/GOOGLE_CALENDAR.md`.
