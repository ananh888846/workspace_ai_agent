# Workspace AI Agent — SECURITY V2

## 1. Credential

Bao gồm OAuth access/refresh token, API key, device credential, webhook secret và encryption key.

Credential phải được mã hóa/bảo vệ và tách khỏi metadata.

Không ghi credential plaintext vào source, Git, log, audit, AgentContext, prompt hoặc error message.

## 2. Credential lifecycle

~~~text
Connect → Secure Store → Authorization → Use → Refresh/Rotate → Revoke → Audit
~~~

Secret chỉ được lấy sau Authorization ALLOW.

## 3. User / Device

Device credential không phải user credential. Face verification hoặc device signal chỉ là input cho identity flow, không tự cấp authorization.

## 4. Logging

Log có request_id để trace nhưng phải mask secret và PII nhạy cảm theo policy. Không log OAuth token, refresh token, API key hoặc device secret.

## 5. Data isolation

Knowledge retrieval, Data Package và Resource Access phải giữ authorization context. Không retrieval rồi mới kiểm tra quyền.

## 6. Provider webhook

Webhook phải kiểm tra signature/secret theo provider contract và chống replay nếu provider hỗ trợ.

## 7. Future hardening

Secret manager, key rotation, encryption at rest, field-level masking, consent, approval workflow, ABAC, rate limit và anomaly detection được thêm theo capability/risk.
