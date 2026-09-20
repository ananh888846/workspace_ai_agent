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
