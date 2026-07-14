from langgraph.prebuilt import ToolNode

from app.tools.knowledge import knowledge_search
from app.tools.user_context import get_user_context
from app.tools.memory import memory_search

tools = [
    knowledge_search,
    get_user_context, 
    memory_search
]

tool_node = ToolNode(tools)