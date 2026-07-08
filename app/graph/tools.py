from langgraph.prebuilt import ToolNode

from app.tools.knowledge import knowledge_search

tools = [
    knowledge_search,
]

tool_node = ToolNode(tools)