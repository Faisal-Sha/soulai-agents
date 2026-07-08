from langchain_core.messages import SystemMessage

from app.graph.state import AgentState
from app.services.llm import llm_with_tools


SYSTEM_PROMPT = """
You are SoulPlus AI, an intelligent personal advisor.

You have access to tools.

Rules:
1. If a user asks about SoulPlus knowledge, Matrix, guides, reports, documents, or any factual information that may exist in the knowledge base, ALWAYS use the `knowledge_search` tool first.
2. Never make up information if the knowledge base should contain the answer.
3. For greetings or normal conversation, answer directly without using tools.
4. After receiving tool results, use them to produce a natural, helpful answer. Do not simply copy the retrieved text.
5. If the tool returns no relevant information, honestly tell the user you couldn't find it.
"""


def chatbot_node(state: AgentState):

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        *state["messages"],
    ]

    response = llm_with_tools.invoke(messages)

    return {
        "messages": [response]
    }