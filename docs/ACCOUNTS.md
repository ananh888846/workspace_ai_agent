# External Accounts V2

## Mục tiêu

Một user có thể có nhiều external account và một external account có thể được chia sẻ có kiểm soát cho user khác.

## Chuẩn

`user_accounts` là mô hình account chuẩn.

```text
users
  └── user_accounts
       ├── Google
       ├── Facebook
       ├── Zalo
       ├── Telegram
       └── ...
```

## Account metadata

Lưu provider, external id, display name, email, status và metadata.

## Credential

Token/secret tách sang `account_credentials`, phải được mã hóa/bảo vệ.

## Resolver

AccountResolver nhận:

- authenticated user;
- provider;
- capability/tool requirement;
- account hint nếu request có chỉ rõ.

Resolver không tự cấp permission.

## Delegation

`account_grants` cho phép user khác sử dụng account trong phạm vi được cấp.

## Multi-account selection

Nếu một user có nhiều account cùng provider và request không xác định account, hệ thống cần policy rõ ràng: default account hoặc yêu cầu user chọn. Không để LLM tự đoán quyền.
