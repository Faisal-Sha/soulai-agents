from typing import Annotated

from langchain.tools import tool
from langgraph.prebuilt import InjectedState

from app.services.user_context import user_context_service


@tool
def get_user_context(
    user_id: Annotated[str, InjectedState("user_id")],
):
    """
    Retrieve the current user's profile, subscription, and personal matrix.
    Use when the user asks about their own data (my matrix, my profile, am I premium, etc.).
    Do not pass a user id — the system provides it automatically.
    """
    try:
        return user_context_service.get_context(user_id)
    except Exception as exc:
        return {"error": f"User context lookup failed: {exc}"}
