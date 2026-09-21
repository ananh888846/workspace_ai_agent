# Authorization V2

## 1. Mục tiêu

Authorization quyết định user có được thực hiện action trên resource hay không. Agent, LLM, LangChain và CrewAI không được bypass.

## 2. Quy trình

~~~text
User
 ↓
Capability Permission
 ↓
Account Grant nếu cần
 ↓
Resource Permission nếu cần
 ↓
Data Package Grant nếu request qua package
 ↓
ALLOW / DENY
~~~

Tất cả điều kiện bắt buộc phải đạt.

## 3. Account Grant

User A sở hữu Google Account A và cấp User B quyền đọc Calendar A:

~~~text
User B
 ↓
calendar.read
 ↓
Account Grant → Google Account A
 ↓
Resource Permission → Calendar A
 ↓
ALLOW
 ↓
Credential
 ↓
Google Calendar Tool
~~~

User B không nhận credential của User A.

## 4. DENY

Thiếu grant hoặc DENY không được suy diễn thành ALLOW.

Khi DENY:
- không lấy secret/refresh token;
- không gọi provider API;
- không chạy protected tool;
- ghi audit theo policy.

## 5. Data Package

Package grant không thay thế resource authorization.

~~~text
Capability
AND Account
AND Resource
AND Package nếu áp dụng
=
ALLOW
~~~

## 6. Ownership

Ownership không tự động cấp quyền cho user khác.

## 7. Multi-account

Nếu user có nhiều account cùng provider, policy phải chọn default account hoặc yêu cầu user chọn. Không để LLM tự đoán.

## 8. Future

Có thể thêm ABAC, consent, approval workflow, field-level access, masking và policy engine.
