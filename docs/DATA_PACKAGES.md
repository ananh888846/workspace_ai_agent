# Data Package / Resource Access V2

## Mục tiêu

Cấp quyền theo dữ liệu thay vì mặc định cấp toàn bộ dữ liệu của một user.

## Model

```text
Data Package
 └── Version
      ├── Resource A
      ├── Resource B
      └── Resource C

Version
 └── Grant → User
```

## Ví dụ

User A có dữ liệu lịch nghỉ học của User C. A tạo package `school_attendance` và grant READ cho User B. User C không có grant thì không được đọc package chỉ vì dữ liệu có liên quan tới C.

## Quy tắc

- Package không thay thế resource authorization; cả hai phải tuân theo policy.
- Grant có thể có thời hạn.
- Version giúp audit thay đổi nội dung package.
- Package không nên chứa credential.
- Package có thể gom resource từ nhiều provider.

## Resolver

Data Package Resolver xác định package nào user được phép dùng trước khi data service truy xuất dữ liệu.

## Tương lai

Có thể mở rộng consent, approval, field-level filtering, masking và policy engine.
