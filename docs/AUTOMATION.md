# Automation V2

## Mục tiêu

Cho phép hệ thống phản ứng với Event theo điều kiện và thực hiện Action.

## Model

```text
Event
 ↓
Trigger
 ↓
Condition
 ↓
Action
```

Ví dụ:

```text
User A về nhà
AND
chưa có medication_taken trong khoảng thời gian policy
↓
nhắc uống thuốc
```

## Domain boundary

Automation không tự bypass authorization. Action phải chạy trong context của owner/user và qua capability/tool policy.

## Agent interaction

Agent có thể đề xuất automation hoặc lập kế hoạch, nhưng việc tạo/chạy automation phải tuân policy.

## Future

Có thể thêm scheduler, retry, idempotency, queue/event bus và approval workflow khi runtime cần scale.
