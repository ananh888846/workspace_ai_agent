# Ví dụ trong app/graphs/scheduling_graph.py
from langgraph.graph import StateGraph

# ... định nghĩa các node và edge ...

# Biến này phải khớp với phần sau dấu hai chấm (:) trong langgraph.json
graph = workflow.compile()
