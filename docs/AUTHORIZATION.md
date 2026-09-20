# Authorization V2

## Mục tiêu

Authorization quyết định user có được thực hiện action trên resource hay không. Agent, LLM, LangChain và CrewAI không được bypass lớp này.

## Mô hình

```text
User
 ↓
Role / Permission
 ↓
Account Grant nếu cần
 ↓
Resource Permission
 ↓
Data Package Grant nếu dữ liệu đi qua package
 ↓
Allow / Deny
```

## Quy tắc

1. Authentication xác định user.
2. Authorization xác định quyền.
3. AccountResolver chỉ tìm account sau khi biết capability cần account.
4. Account ownership không tự động cấp quyền cho user khác.
5. Grant có thể có thời hạn và trạng thái.
6. Deny hoặc thiếu grant không được suy diễn thành allow.
7. Mọi access nhạy cảm phải có audit.

## Account delegation

User A sở hữu Google Account A. User B được grant chỉ đọc Calendar A.

```text
User B
 ↓
calendar.read
 ↓
Google Account A
 ↓
Calendar resource
 ↓
ALLOW
```

Không có nghĩa User B có toàn bộ quyền của User A.

## Data Package access

Package là lớp quyền cấp theo dữ liệu. Một package có thể gồm nhiều resource và có version. User nhận package thông qua grant.

## Future extension

Có thể bổ sung ABAC/policy engine, consent, approval workflow và field-level access mà không thay đổi nguyên tắc core.
