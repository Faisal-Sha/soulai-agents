from langgraph.prebuilt import ToolNode

from app.tools.knowledge import knowledge_search
from app.tools.user_context import get_user_context
from app.tools.memory import memory_search
from app.tools.destiny_matrix import (
    calculate_destiny_matrix,
    calculate_compatibility_matrix,
)

tools = [
    knowledge_search,
    get_user_context,
    memory_search,
    calculate_destiny_matrix,
    calculate_compatibility_matrix,
]

tool_node = ToolNode(tools)