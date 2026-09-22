# Workspace AI Agent — Execution Contract V1

> Contract chuẩn hóa kết quả thực thi của Agent sau Calendar V1.

## 1. Mục tiêu

Execution Contract là lớp hợp đồng chung để các capability như Calendar, Gmail, Drive, Zalo, Facebook, Home Assistant và các capability tương lai trả kết quả theo cùng một cấu trúc.

Contract này không thay thế Authorization, Credential, Tool hoặc Provider. Nó chỉ chuẩn hóa thông tin mà các tầng đó đã quyết định.

## 2. Execution flow

```text
Request
  ↓
Classification
  ↓
Account Resolution
  ↓
Authorization
  ↓
Credential Resolution
  ↓
Capability / Graph
  ↓
Tool
  ↓
Provider
  ↓
Result Contract
```

`ExecutionContract` mô tả execution path; `ResultContract` mô tả kết quả capability; `ErrorContract` mô tả lỗi có cấu trúc.

## 3. Execution Contract

Mẫu chuẩn:

```json
{
  "intent": "calendar",
  "capability": "calendar.read",
  "action": "read",
  "account": {
    "status": "resolved"
  },
  "authorization": {
    "status": "allow"
  },
  "credential": {
    "status": "ready"
  },
  "provider_called": true
}
```

### Trường bắt buộc

| Trường | Ý nghĩa |
|---|---|
| `intent` | Nhóm ý định nghiệp vụ |
| `capability` | Capability được route |
| `action` | Hành động cụ thể |
| `account` | Trạng thái account resolution |
| `authorization` | Kết quả authorization |
| `credential` | Trạng thái credential |
| `provider_called` | Provider có thực sự được gọi hay chưa |

`provider_called` là execution fact, không phải suy đoán từ `status`.

## 4. Result Contract

Kết quả capability có dạng:

```json
{
  "status": "ok",
  "action": "list_events",
  "data": {},
  "error": null,
  "provider_called": true
}
```

Khi lỗi:

```json
{
  "status": "confirmation_required",
  "action": "delete_event",
  "data": null,
  "error": {
    "code": "confirmation_required",
    "message": "Cần xác nhận trước khi xóa sự kiện.",
    "retryable": false,
    "provider_called": false,
    "details": null
  },
  "provider_called": false
}
```

## 5. Error Contract

`ErrorContract` gồm:

- `code`: machine-readable code ổn định;
- `message`: thông báo cho application/API;
- `retryable`: lỗi có thể retry hay không;
- `provider_called`: provider đã được gọi hay chưa;
- `details`: metadata có cấu trúc, nếu cần.

Không đưa secret, OAuth token hoặc dữ liệu nhạy cảm vào `message` hoặc `details`.

## 6. Status chuẩn V1

- `not_classified`
- `account_not_found`
- `account_selection_required`
- `authorization_denied`
- `oauth_required`
- `validation_error`
- `confirmation_required`
- `provider_error`
- `unsupported_action`
- `ok`

Các module hiện tại có thể còn dùng alias nội bộ như `not_found` hoặc `deny`; `normalize_result_status()` là điểm chuẩn hóa về contract.

## 7. Quy tắc provider boundary

### Trước provider call

Nếu gặp:

- account không tồn tại;
- account chưa được chọn;
- authorization denied;
- credential chưa sẵn sàng;
- validation error;
- confirmation chưa đủ;
- action không hỗ trợ;

thì `provider_called` phải là `false`.

### Sau provider call

Nếu provider đã được gọi và xảy ra lỗi provider, result phải thể hiện:

```json
{
  "status": "provider_error",
  "provider_called": true
}
```

Không được biến provider error thành `validation_error`.

## 8. Confirmation

Các thao tác có side effect nhạy cảm phải có trạng thái `confirmation_required` trước khi gọi provider.

Calendar Delete V1 là reference implementation:

```text
confirmed=false
    ↓
confirmation_required
    ↓
provider_called=false
```

## 9. Retry

`retryable=true` chỉ dùng cho lỗi mà application có thể retry an toàn.

Ví dụ có thể retry:
- provider timeout;
- lỗi mạng tạm thời;
- provider rate limit nếu policy cho phép.

Không mặc định retry:
- authorization denied;
- validation error;
- account_not_found;
- confirmation_required;
- unsupported_action.

## 10. Không tạo migration database

Execution Contract V1 là application/runtime contract. Chưa tạo bảng mới và chưa thay đổi database schema.

Audit/Agent Run persistence sẽ được thiết kế riêng khi domain Audit/Agent Run được triển khai.

## 11. Không dùng thêm framework

Implementation V1 dùng Python `dataclass` và `StrEnum`.

Không thêm LangGraph hoặc Pydantic chỉ để tạo contract này. LangGraph tiếp tục là orchestration framework đã chốt; Pydantic chỉ được dùng khi boundary thực sự cần theo các Decision hiện hành.

## 12. Reference implementation

Calendar V1 là reference implementation cho:

```text
AccountResolver
 → AuthorizationService
 → CredentialResolver
 → Tool
 → Provider
 → Result
```

Các capability sau phải cố gắng tái sử dụng Execution Contract thay vì tạo response shape riêng.

## 13. Acceptance criteria

Execution Contract V1 được coi là đạt khi:

1. Có module contract dùng chung.
2. Có status chuẩn.
3. Có Result Contract và Error Contract.
4. Có test contract độc lập.
5. Không thay đổi database.
6. Không bypass Authorization/Credential/Tool/Provider boundary.
7. Calendar V1 tiếp tục chạy regression suite không bị thay đổi hành vi.
