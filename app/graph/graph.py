from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import tools_condition
#  if want to visualize the graph use below imports
# from IPython import Image, display 

from app.graph.tools import tool_node
from app.graph.node import chatbot_node
from app.graph.state import AgentState

builder = StateGraph(AgentState)

# Nodes
builder.add_node("chatbot", chatbot_node)
builder.add_node("tools", tool_node)

# Start
builder.add_edge(START, "chatbot")

# Conditional edge: tool call -> tools, otherwise -> end
builder.add_conditional_edges(
    "chatbot",
    tools_condition,
    {"tools": "tools", END: END},
)

# After tool execution, go back to chatbot
builder.add_edge("tools", "chatbot")

graph = builder.compile()






