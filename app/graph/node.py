from langchain_core.messages import SystemMessage

from app.graph.state import AgentState
from app.prompts.system_prompt import build_system_prompt
from app.services.llm import llm_with_tools


def assistant_node(state: AgentState):
    """
    Assistant node = orchestration only.

    Steps:
      1) Build system prompt (language-aware)
      2) Call the LLM (with tools bound)
      3) Return the AI message

    No clarification logic here.
    No slot filling.
    No pending-task database work.
    Those belong in services + /chat.
    """
    user_language = state.get("user_language", "en")
    system_prompt = build_system_prompt(user_language)

    messages = [
        SystemMessage(content=system_prompt),
        *state["messages"],
    ]

    response = llm_with_tools.invoke(messages)

    return {
        "messages": [response],
    }
