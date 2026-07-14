# this is tool to fetch user facts from supabase
from typing import Annotated

from langchain.tools import tool
from langgraph.prebuilt import InjectedState

from app.services.memory_service import memory_service


@tool
def memory_search(
    user_id: Annotated[str, InjectedState("user_id")],
):
    """
    Search the user's long-term memories and facts previously shared.
    Use when the user asks what you remember, their goals, preferences, or past details.
    Do not pass a user id — the system provides it automatically.
    """
    try:
        return memory_service.search_memories(user_id) or []
    except Exception as exc:
        return {"error": f"Memory search failed: {exc}"}

