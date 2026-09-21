# Agents V2

## Agent types dự kiến

- General Agent
- Knowledge Agent
- Activity Agent
- Medication Agent
- Device Agent
- Workflow/Multi-Agent orchestration

## Nguyên tắc

Agent nhận AgentContext đã được kiểm soát. Agent không tự bypass authorization.

Agent có thể gọi capability/tool đã được cấp.

LLM có thể phân loại intent và tạo plan, nhưng permission là quyết định của application policy.

## Multi-agent

CrewAI có thể quản lý collaboration giữa specialist agents. LangChain có thể cung cấp model/tool/retrieval primitives. Không đưa business authorization vào framework-specific code.

## Agent Run

Mỗi execution quan trọng nên có request_id/agent_run_id và tool_run để trace.


## Multi-agent communication V2.1

Agent-to-Agent collaboration dùng ba lớp:

- Agent Message: envelope giao tiếp.
- Agent Task: công việc Agent A giao Agent B, có parent task/request trace.
- Agent Permission: policy cho phép Agent nào được giao capability/action nào cho Agent nào.

Luồng chuẩn:

`Agent A → Agent Task/Message → Agent Router → Authorization → Agent B → Result/Trace`

Agent-to-Agent permission không thay thế user authorization. Agent B vẫn phải kiểm tra AgentContext và policy trước khi gọi tool/provider.

Mỗi message/task phải gắn request_id; execution có side effect phải liên kết agent_run/tool_run khi phù hợp.
