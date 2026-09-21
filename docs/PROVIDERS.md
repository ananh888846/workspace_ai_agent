# Providers V2

## Mục tiêu

Chuẩn hóa cách kết nối external services mà không làm Agent Core phụ thuộc provider.

## Provider dự kiến

- Google: Gmail, Drive, Calendar
- Facebook/Meta
- TikTok
- Instagram
- Zalo
- Telegram
- Home Assistant
- các provider tương lai

## Adapter model

```text
Capability
 ↓
Tool Resolver
 ↓
Provider Adapter
 ↓
External API
```

## Google phase đầu

Google là provider đầu tiên để kiểm chứng account resolver, credentials, resource access và tool execution.

## Future providers

Mỗi provider cần contract rõ cho account, credential, resource mapping, webhook/sync nếu có và rate-limit/error policy.

## Không làm ở Core

Không hard-code Facebook/Zalo/Google logic vào Agent Orchestrator. Provider-specific behavior nằm trong provider/tool layer.
