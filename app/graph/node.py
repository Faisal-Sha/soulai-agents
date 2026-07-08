from langchain_core.messages import SystemMessage

from app.graph.state import AgentState
from app.prompts.system_prompt import build_system_prompt
from app.services.llm import llm_with_tools


def chatbot_node(state: AgentState):
    user_language = state.get("user_language", "en")
    system_prompt = build_system_prompt(user_language)

    messages = [
        SystemMessage(content=system_prompt),
        *state["messages"],
    ]

    response = llm_with_tools.invoke(messages)

    return {
        "messages": [response]
    }
