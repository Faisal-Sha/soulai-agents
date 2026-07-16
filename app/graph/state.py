from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    State that flows through the LangGraph.

    Keep this small on purpose.
    Business logic (clarification, memory save, pending tasks)
    lives in services + the /chat endpoint — NOT in the graph.
    """

    # Full chat messages for this turn (history + new user message)
    messages: Annotated[list, add_messages]

    # "en" or "ru" — used to build the system prompt language
    user_language: str

    # Authenticated user id — injected into tools via InjectedState
    user_id: str
