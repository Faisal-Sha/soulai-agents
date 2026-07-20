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
    (goals, family names, preferences, projects, friend DOBs / friend Destiny Matrices,
    and previous compatibility readings).

    Use for remembered chat facts, previously calculated friend/relative matrices
    (keys like person_sarah_relation, person_sarah_dob, person_sarah_matrix), and
    compatibility facts (compat_me_sarah_matrix, compat_ali_sara_summary).
    Do NOT use for THIS user's own Destiny Matrix energies, DOB, profile,
    or subscription — those come from get_user_context.

    Never guess; call this tool when remembered information is needed.
    Do not pass a user id — the system injects it.
    """
    try:
        return memory_service.search_memories(user_id) or []
    except Exception as exc:
        return {"error": f"Memory search failed: {exc}"}
