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


## 2026-09-21 — Local Calendar DB fixture hardening
- Kiểm tra các migration 001–011 liên quan đến tenant, user, membership, account, credentials, roles, permissions và resources.
- Điều chỉnh `scripts/calendar/bootstrap_test_data.sql` để idempotent hơn khi chạy lại.
- Google account fixture chuyển sang trạng thái `pending_oauth` với external ID cục bộ, tránh giả lập một Google account đã xác thực.
- Fixture không tạo `account_credentials`, access token, refresh token hoặc fake Calendar resource.
- Thêm các truy vấn verification cho tenant/user/account/permissions.
- Cập nhật `docs/GOOGLE_CALENDAR.md` với quy trình seed local PostgreSQL và các dữ liệu cố ý không được tạo.
- Không tạo Migration 052.
- Không lưu OAuth secret/token trong repository.


## 2026-09-21 — Configuration V1 baseline
- Thêm `.env.example` làm template cấu hình local, không chứa secret thật.
- Thêm `.gitignore` để loại `.env`, runtime data, Python cache và local storage khỏi Git.
- Thêm `app/config/settings.py` và `app/config/__init__.py` làm central configuration layer.
- Thêm `docs/CONFIGURATION.md` để ghi rõ nhóm cấu hình, secret boundary và thứ tự triển khai.
- PostgreSQL, Qdrant, Ollama và File Storage có cấu hình baseline.
- Google OAuth chỉ được đánh dấu `configured` khi có Client ID + Client Secret; chưa yêu cầu OAuth để Agent khởi động.
- OAuth access/refresh token không được lưu trong `.env`; credential của từng external account vẫn thuộc `account_credentials` và CredentialResolver.
- Chưa thay đổi Docker Compose vì repository hiện chưa có `docker-compose.yml` được quản lý trên GitHub.


## 2026-09-21 — Google OAuth local file layout
- Chốt thư mục local `data/google/` cho Google OAuth bootstrap.
- `credentials.json` là OAuth client configuration từ Google Cloud, không phải credential của một user cụ thể.
- `token.json` là local runtime token nếu OAuth flow sử dụng file token.
- Cả `credentials.json` và `token.json` đều không được commit.
- Thêm `GOOGLE_CREDENTIALS_FILE` và `GOOGLE_TOKEN_DIR` vào `.env.example` và `app/config/settings.py`.
- Cập nhật `docs/CONFIGURATION.md` với mapping local → Docker: `data/google/` → `/app/data/google/`.
- Chưa chạy OAuth và chưa tạo token thật.


## 2026-09-21 — Docker infrastructure configuration baseline
- Thêm `docker-compose.yml` quản lý PostgreSQL 18 và Qdrant với named volumes.
- Bổ sung biến `POSTGRES_*` và `QDRANT_*_HOST_PORT` vào `.env.example`.
- Cập nhật `docs/CONFIGURATION.md` về boundary giữa infrastructure container và application runtime.
- Chưa thêm Agent application service vào Compose vì source tree hiện chưa có `app/main.py` và Dockerfile runtime hoàn chỉnh trên GitHub.
- Chốt không copy `credentials.json` vào Docker image; application runtime sau này sẽ mount `data/google/` vào `/app/data/google/` theo policy secret.


## 2026-09-21 — PostgreSQL AccountResolver repository V1
- Thêm `app/infrastructure/database/repositories/accounts.py` triển khai `AccountRepository.find_candidates()` trên PostgreSQL.
- AccountResolver chỉ đọc metadata từ `user_accounts`; không đọc `account_credentials` và không resolve secret.
- Hỗ trợ account ownership và delegated account qua `account_grants`, có tenant/membership và thời hạn grant.
- Account hint chỉ exact-match theo account ID, external account ID hoặc email; không fuzzy-match.
- Thêm unit tests cho mapping metadata và exact hint parameterization.
- Cập nhật `docs/GOOGLE_CALENDAR.md` với runtime status và gate tiếp theo.
- Chưa tạo Migration 052; chưa gọi OAuth hoặc Google Calendar API.


## 2026-09-21 — Phase 2A — Agent HTTP contract
- Thêm app/main.py với FastAPI và POST /api/v1/agent/chat.
- Thêm app/api/schemas.py và app/api/chat.py làm HTTP/application boundary.
- Endpoint chưa gọi LLM, credential, tool hoặc provider; provider_called=false được trả về rõ ràng.
- Thêm unit/API tests cho health, conversation_id và account_hint.
- Thêm docs/API_PHASE2.md.
- Bổ sung runtime dependencies trong requirements.txt.
- Phase 2A = DONE. Phase 2B bắt đầu bằng AccountResolver runtime wiring.


## 2026-09-21 — Phase 2B — AccountResolver runtime wiring
- Thêm database connection boundary bằng psycopg.
- Nối POST /api/v1/agent/chat với PostgresAccountRepository + AccountResolver khi request có account_hint.
- Bổ sung X-User-ID và X-Organization-ID làm AgentContext test/runtime context; không tự cấp quyền.
- Xử lý account_not_found và account_selection_required.
- Không đọc account_credentials, không authorize và không gọi provider.
- Bổ sung API tests và đồng bộ docs/API_PHASE2.md.
- Phase 2B = DONE. Phase 2C = PostgreSQL Authorization runtime.


## 2026-09-21 — Phase 2C — PostgreSQL Authorization runtime

- Thêm app/infrastructure/database/repositories/permissions.py triển khai PostgreSQL PermissionRepository.
- Capability permission được resolve qua user_roles → role_permissions → permissions.
- Account access kiểm tra account ownership hoặc account_grants active, cùng Organization và còn hiệu lực.
- Resource access kiểm tra resource_permissions với tenant membership, action, effect=allow và expiry.
- Không đọc account_credentials; credential/provider vẫn nằm sau Authorization gate.
- Mở rộng POST /api/v1/agent/chat với capability, action, target_resource.
- Runtime flow: AccountResolver → AuthorizationService → PostgreSQL PermissionRepository → ALLOW/DENY.
- Bổ sung unit/API tests cho PostgreSQL authorization repository và Phase 2C HTTP wiring.
- Đồng bộ docs/API_PHASE2.md và docs/GOOGLE_CALENDAR.md.
- Phase 2C = DONE. Phase 2D = nối Web Chat vào real Agent API.

## 2026-09-21 — Fix local runtime loading of .env

- Xác định Agent chạy trực tiếp bằng Uvicorn trên Windows không tự có biến `DATABASE_URL` từ file `.env`, khiến AccountResolver trả HTTP 500 với `DATABASE_URL is not configured`.
- Cập nhật `app/config/settings.py` để tự đọc `.env` tại root project khi process chưa có biến tương ứng.
- Environment variables được inject sẵn luôn được ưu tiên và không bị `.env` ghi đè.
- Cập nhật `docs/CONFIGURATION.md` để phân biệt PostgreSQL endpoint khi Agent chạy ngoài Docker (`127.0.0.1:5433`) và hostname trong Docker network.
- Không thêm dependency mới và không thay đổi schema/migration.

## 2026-09-21 — Quy tắc ngôn ngữ ghi chú Python

- Chốt nguyên tắc: mọi comment, docstring và ghi chú trong file `.py` phải viết bằng **tiếng Việt**.
- Các tên kỹ thuật bắt buộc như tên biến/hàm, package, class, API, exception, protocol và framework được giữ nguyên.
- Cập nhật `docs/ARCHITECTURE.md` để khóa nguyên tắc này trong kiến trúc chính thức.
- Quy tắc áp dụng cho code Python mới và các phần được chỉnh sửa về sau.

## 2026-09-21 — Chuẩn hóa ghi chú Python theo quy tắc tiếng Việt

- Chuyển các docstring tiếng Anh hiện có trong `app/config/settings.py` sang tiếng Việt.
- Không thay đổi logic cấu hình hoặc hành vi runtime.
- Đây là bước kiểm tra thực thi đầu tiên sau khi khóa quy tắc ngôn ngữ ghi chú Python.

## 2026-09-21 — Fix PostgreSQL AccountResolver query

- Sửa truy vấn `PostgresAccountRepository.find_candidates()` để tương thích PostgreSQL khi kết hợp `SELECT DISTINCT` với `ORDER BY`.
- Đưa phần loại trùng vào subquery rồi sắp xếp ở truy vấn ngoài, giữ nguyên kết quả và thứ tự hiển thị mong muốn.
- Chuẩn hóa các docstring/comment trong file Python vừa chỉnh sửa sang tiếng Việt theo quy tắc đã chốt.
- Không thay đổi schema, migration hoặc authorization contract.


## 2026-09-21 — Fix AccountResolver với account pending_oauth

- Xác định nguyên nhân `account_not_found`: PostgreSQL AccountResolver chỉ lọc `user_accounts.status = 'active'`, trong khi Calendar local fixture cố ý dùng `pending_oauth` để biểu diễn account chưa có OAuth credential.
- Sửa `PostgresAccountRepository.find_candidates()` cho phép resolve metadata của account có trạng thái `active` hoặc `pending_oauth`.
- Giữ nguyên boundary: `pending_oauth` chỉ cho phép resolve metadata và đi qua Authorization; không được xem là credential hợp lệ và không được bypass CredentialResolver.
- Sửa Agent HTTP runtime để giữ nguyên trạng thái thật của account sau AccountResolver, thay vì chuyển mọi account thành `active`.
- Chuẩn hóa các docstring tiếng Anh trong `app/application/core_runtime.py` sang tiếng Việt theo quy tắc Python đã chốt.
- Đồng bộ `docs/GOOGLE_CALENDAR.md`, `docs/API_PHASE2.md` và `docs/ARCHITECTURE.md`.
- Không tạo Migration 052 và không thay đổi schema.


## 2026-09-21 — Fix Authorization account access với pending_oauth

- Xác định nguyên nhân Calendar Authorization trả `account_access_denied`: `PostgresPermissionRepository.has_account_access()` chỉ cho account owner có trạng thái `active`, trong khi local Calendar fixture cố ý dùng `pending_oauth`.
- Sửa kiểm tra account ownership và delegated account để chấp nhận metadata account ở trạng thái `active` hoặc `pending_oauth`.
- Giữ nguyên boundary: `pending_oauth` không phải credential readiness; sau Authorization = ALLOW vẫn phải đi qua CredentialResolver/OAuth.
- Chuyển comment tiếng Anh còn lại trong `permissions.py` sang tiếng Việt theo quy tắc Python của project.
- Bổ sung unit test xác nhận `pending_oauth` được chấp nhận ở account access và không truy cập `account_credentials`.
- Đồng bộ `docs/API_PHASE2.md` và `docs/GOOGLE_CALENDAR.md`.
- Không tạo Migration 052, không tạo credential giả và không bypass Authorization.
