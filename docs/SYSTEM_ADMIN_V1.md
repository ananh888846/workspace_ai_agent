# System Administrator V1

**Cập nhật:** 2026-09-23 20:00 (GMT+7, TP.HCM)

## 1. Trạng thái

**IMPLEMENTED_GITHUB — LOCAL VERIFICATION PENDING**

System Administrator V1 dùng mô hình:

Human User → system_admin Role → role_permissions → Permission catalog.

Không tạo Principal/User type riêng cho Admin.

## 2. Permission catalog

Khi bootstrap system_admin, role được gắn **tất cả Permission hiện có tại thời điểm chạy** bằng các bản ghi role_permissions.

Đây là explicit mapping, không có wildcard permission.

Khi hệ thống bổ sung Permission mới:

1. Permission mới phải được review/duyệt.
2. Permission được thêm vào catalog.
3. Chạy lại bootstrap system_admin hoặc thao tác tương đương để map Permission mới.
4. Không thay đổi Authorization logic để tạo quyền vượt boundary.

## 3. Organization scope

system_admin không bypass Organization/Tenant Authorization.

User Admin phải là member của Organization đang xử lý request. Một User có thể được membership ở nhiều Organization nếu policy sau này cho phép.

Bootstrap mặc định tạo hoặc dùng một Organization có organization_type = system, với tên do người triển khai truyền vào.

Không dùng Local Calendar Test.

## 4. User Admin

Bootstrap nhận:

- ADMIN_NAME
- ADMIN_EMAIL
- ADMIN_ORG_NAME

Nếu email Admin đã tồn tại trong Agent:

- giữ nguyên User ID;
- không remap User;
- chỉ bảo đảm membership và role mapping cần thiết.

Bootstrap không nhận và không lưu:

- password Web;
- Laravel session;
- OAuth access token;
- OAuth refresh token;
- API key;
- credential secret.

## 5. Chạy local

Ví dụ PowerShell:

~~~text
psql "$env:DATABASE_URL" -v ADMIN_NAME="Administrator" -v ADMIN_EMAIL="admin@example.com" -v ADMIN_ORG_NAME="Workspace Administration" -f scripts/bootstrap_system_admin_v1.sql
~~~

Nếu PowerShell đang dùng DATABASE_URL khác, thay bằng connection string PostgreSQL thực tế.

Kết quả cuối phải trả:

- admin_user_id;
- admin_organization_id;
- system_admin_role_id;
- số Permission được map.

**Không gửi password Admin vào chat.**

## 6. Kiểm tra sau bootstrap

~~~sql
SELECT u.id, u.name, u.email, u.status
FROM users u
WHERE u.email = 'admin@example.com';

SELECT r.name, count(*) AS permission_count
FROM user_roles ur
JOIN roles r ON r.id = ur.role_id
JOIN role_permissions rp ON rp.role_id = r.id
JOIN permissions p ON p.id = rp.permission_id
JOIN users u ON u.id = ur.user_id
WHERE u.email = 'admin@example.com'
  AND r.name = 'system_admin'
GROUP BY r.name;
~~~

Đối chiếu permission_count với:

~~~sql
SELECT count(*) FROM permissions;
~~~

Hai số phải bằng nhau tại thời điểm bootstrap.

## 7. Liên kết với Laravel Web

Sau khi có admin_user_id, Web dùng chính ID này làm:

~~~env
AUTH_ADMIN_AGENT_USER_ID=<admin_user_id>
~~~

Laravel vẫn chỉ giữ mapping auth_users.agent_user_id.

Không tạo User/Identity source thứ hai cho Agent.

## 8. Giới hạn V1

"Toàn quyền" ở V1 có nghĩa:

> toàn bộ Permission catalog đã được định nghĩa và map cho role system_admin tại thời điểm bootstrap.

Nó không có nghĩa:

- bypass Authorization;
- bỏ qua Organization membership;
- tự động truy cập mọi Organization;
- tự động tạo Permission chưa được định nghĩa;
- cho LLM quyền quyết định;
- biến Admin thành credential root của PostgreSQL.

Guest Access vẫn Deferred theo Decision 051.

## 9. Acceptance

Acceptance SQL:

database/tests/acceptance_system_admin_v1.sql

Kiểm tra:

- Human User + Organization + membership;
- Role system_admin;
- explicit Permission mapping;
- không có wildcard permission;
- role không tự thay thế Organization membership.

## 10. Trạng thái

Sau khi GitHub merge:

**IMPLEMENTED_GITHUB — LOCAL VERIFICATION PENDING**

Chỉ chuyển sang LOCAL_VERIFIED sau khi đúng commit được pull về local và chạy bootstrap/acceptance thành công.
