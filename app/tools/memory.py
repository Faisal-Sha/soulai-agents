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
    Retrieve long-term memories and life facts the user previously shared in conversation
    (goals, family names, preferences, projects, "what do you know about me").

    Use for remembered chat facts. Do NOT use for Destiny Matrix energies, DOB, profile,
    or subscription — those come from get_user_context.

    Never guess; call this tool when remembered information is needed.
    Do not pass a user id — the system injects it.
    """
    try:
        return memory_service.search_memories(user_id) or []
    except Exception as exc:
        return {"error": f"Memory search failed: {exc}"}
