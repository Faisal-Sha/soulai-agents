"""
LangGraph definition — keep this tiny.

  START → chatbot ⇄ tools → END

Clarification / pending tasks / memory save are NOT graph nodes.
They are handled in app/api/chat.py + services/.
"""

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import tools_condition
from langgraph.checkpoint.memory import MemorySaver
# If you want to visualize the graph later:
# from IPython.display import Image, display

from app.graph.tools import tool_node
from app.graph.node import assistant_node
from app.graph.state import AgentState

builder = StateGraph(AgentState)

# Nodes (orchestration only)
builder.add_node("chatbot", assistant_node)
builder.add_node("tools", tool_node)

builder.add_edge(START, "chatbot")

# If the model requested tools → run tools, else finish
builder.add_conditional_edges(
    "chatbot",
    tools_condition,
    {"tools": "tools", END: END},
)

# After tools, go back to the chatbot with tool results
builder.add_edge("tools", "chatbot")

# In-memory checkpointer (per process). Durable chat lives in Supabase.
memory = MemorySaver()

graph = builder.compile(
    checkpointer=memory
)






