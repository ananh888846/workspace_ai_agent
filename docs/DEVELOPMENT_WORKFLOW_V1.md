# QUY TRÌNH PHÁT TRIỂN V1

**Cập nhật:** 2026-09-23 09:35 (GMT+7, TP.HCM)

## 1. Mục đích

Tài liệu này quy định quy trình bắt buộc khi phát triển `workspace_ai_agent` và tích hợp với `workspace_ai_agent_web`.

## 2. Ranh giới hai repository

### `workspace_ai_agent`

Đây là hệ thống Agent/Core và miền dữ liệu PostgreSQL của Agent. Trong các công việc tích hợp Web, repository này được xem là **chỉ đọc**, trừ khi người dùng cho phép sửa rõ ràng.

Không được tự ý thêm, xóa hoặc sửa code Agent, schema database, migration, API, cơ chế authentication hoặc tài liệu của Agent.

### `workspace_ai_agent_web`

Đây là repository triển khai Web/Laravel. Thay đổi Web phải tích hợp theo contract hiện có của Agent, không âm thầm thay đổi repository Agent để làm cho Web chạy được.

## 3. Quy trình bắt buộc

Mọi thay đổi quan trọng phải đi theo đúng thứ tự:

### Bước 1 — Phân tích

- Kiểm tra code hiện tại, schema/database, API contract, cấu hình, test và tài liệu liên quan.
- Xác định ranh giới repository và dependency trước khi sửa.

### Bước 2 — Thực hiện code trên GitHub

- Chỉ sửa repository và branch đã được xác định.
- Không sửa repository còn lại chỉ để làm cho test chạy được.

### Bước 3 — Đồng bộ tài liệu

Nếu thay đổi làm ảnh hưởng đến kiến trúc, hành vi, API, cấu hình, bảo mật, database hoặc vận hành thì phải cập nhật tài liệu **trong cùng đợt thay đổi**.

Tài liệu phải mô tả đúng implementation đã commit, không mô tả một trạng thái dự kiến trong tương lai.

### Bước 4 — Báo trạng thái GitHub

Phải báo rõ cho người dùng:

- repository;
- branch;
- commit;
- file/hành vi đã thay đổi.

Phải nói rõ:

> **ĐÃ CẬP NHẬT GITHUB — KÉO CODE VỀ LOCAL TRƯỚC KHI TEST.**

### Bước 5 — Kéo về local

Người dùng đồng bộ branch đã thay đổi về local.

Không được coi thay đổi trên GitHub là đã kiểm thử local cho đến khi đúng commit đã được kéo về local.

### Bước 6 — Kiểm tra local

- Xác nhận branch và commit.
- Kiểm tra `git status` và diff liên quan.
- Chỉ cài/cập nhật dependency khi cần.
- Chỉ chạy migration/cập nhật cấu hình khi cần và sau khi kiểm tra tác động.
- Chạy unit test, integration test, smoke test, API test, browser test hoặc end-to-end test phù hợp.

### Bước 7 — Báo cáo kiểm tra

Phải báo:

- commit chính xác đã test;
- các lệnh đã chạy;
- kết quả test;
- lỗi còn lại;
- giới hạn hoặc điều kiện chưa kiểm tra được.

Không được tuyên bố hoàn thành chỉ vì code đã tồn tại trên GitHub.

### Bước 8 — Chốt

Một thay đổi chỉ có trạng thái `FINAL` khi code và tài liệu đã đồng bộ, commit tương ứng đã được kiểm tra local thành công, hoặc người dùng đã chấp nhận rõ ràng một ngoại lệ có ghi nhận.

## 4. Vòng đời trạng thái

- `PROPOSED` — mới phân tích/đề xuất.
- `IMPLEMENTED_GITHUB` — đã commit trên GitHub nhưng chưa kiểm tra local.
- `LOCAL_VERIFIED` — đúng commit đã được kéo về local và test đạt.
- `FINAL` — code, tài liệu và kiểm tra đã hoàn tất.
- `BLOCKED` — bị chặn bởi lỗi kiểm tra hoặc dependency/kiến trúc cần quyết định.

## 5. Quy tắc database và authentication

- Không tạo nguồn dữ liệu User thứ hai cho Agent nếu chưa được cho phép.
- Không tạo SQLite riêng cho authentication Web khi kiến trúc được duyệt yêu cầu PostgreSQL/API của Agent.
- Không copy User của Agent sang bảng credential riêng của Web nếu chưa được cho phép.
- Không vượt qua ranh giới API/bảo mật của Agent bằng cách sửa repository Agent chỉ để đơn giản hóa việc triển khai Web.

## 6. Quy tắc ngôn ngữ và thời gian cho tài liệu Markdown

Tất cả file `.md` trong hai repository phải tuân thủ:

1. **Ưu tiên tiếng Việt.** Nội dung phải viết bằng tiếng Việt nếu có thể diễn đạt rõ ràng.
2. Tiếng Anh chỉ dùng khi thuật ngữ kỹ thuật, tên API/code, tên sản phẩm, tên thư viện hoặc cách diễn đạt tiếng Việt có thể gây mơ hồ.
3. Không dịch các identifier như class, function, variable, route, table, column, command, environment variable và code.
4. Mỗi file `.md` phải có dòng thời gian cập nhật theo mẫu:

   `**Cập nhật:** YYYY-MM-DD HH:mm (GMT+7, TP.HCM)`

5. Khi sửa nội dung file `.md`, phải cập nhật lại timestamp.
6. Múi giờ chuẩn của tài liệu là `Asia/Ho_Chi_Minh` / `GMT+7`.

## 7. Kỷ luật thay đổi

Trước mỗi thay đổi phải xác định repository nào được sửa và lý do.

Nếu một yêu cầu không thể thực hiện mà không sửa repository còn lại, phải dừng và hỏi người dùng. Không được tự ý sửa repository còn lại.

## 8. Điều kiện hoàn thành

Một thay đổi chỉ được coi là hoàn thành khi:

- sửa đúng repository;
- tôn trọng ranh giới giữa hai repository;
- tài liệu liên quan đã được đồng bộ;
- người dùng đã được báo phải kéo commit GitHub về local;
- đúng commit đã được kiểm tra local;
- kết quả và giới hạn kiểm tra đã được ghi nhận;
- và mọi ngoại lệ còn lại đã được người dùng chấp nhận rõ ràng.
