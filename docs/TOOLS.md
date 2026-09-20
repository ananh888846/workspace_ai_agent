# Tools / Capabilities V2

## Phân biệt

Capability mô tả khả năng nghiệp vụ.

Tool là implementation dùng để thực thi capability.

Ví dụ:

```text
Capability: calendar.read
        ↓
Tool Resolver
        ↓
Google Calendar Tool
```

## Tool Definition

Một tool definition cần mô tả tối thiểu:

- capability;
- provider;
- resource;
- action;
- requires_account;
- input/output contract.

## Registry

Tool Registry là nơi mapping capability → implementation. Provider-specific details không được lan lên Agent Core.

## Account dependency

Nếu `requires_account=false`, request không cần external account.

Nếu `requires_account=true`, AccountResolver phải chạy trước tool execution.

## Security

Tool không tự quyết định authorization. Tool chỉ chạy sau khi application đã authorize.
