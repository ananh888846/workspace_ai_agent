# Memory V2

## Phân biệt

Conversation lưu lịch sử hội thoại.

Memory lưu thông tin Agent cần nhớ lâu hơn hội thoại.

Knowledge lưu tài liệu/dữ liệu để retrieval.

Data Package xác định user được phép truy cập dữ liệu nào.

## Memory types dự kiến

- short_term
- long_term
- preference
- fact
- instruction

## Nguyên tắc

- Không biến mọi message thành memory.
- Memory có source và lifecycle.
- Memory có thể có importance/priority.
- Memory phải chịu authorization khi liên quan dữ liệu user.
- Knowledge retrieval không tự động ghi vào personal memory.

## Runtime

Short-term context có thể nằm trong memory/cache của Agent; long-term memory lưu database và có thể được index nếu cần. Chi tiết tối ưu runtime sẽ được quyết định sau khi benchmark thực tế.
