from typing import Annotated

from langchain.tools import tool
from langgraph.prebuilt import InjectedState

from app.services.user_context import user_context_service


@tool
def get_user_context(
    user_id: Annotated[str, InjectedState("user_id")],
):
    """
    Fetch THIS authenticated user's profile, DOB, subscription, and personal Destiny Matrix.

    Use FIRST (before Knowledge) whenever the question is about their own data:
    my matrix, my destiny matrix, my matrix values, my DOB/birth date, my center/money/love/
    health energy, my profile, premium/subscription/report, or short replies like "yes"
    after they asked for their matrix.

    Returns personal matrix_data (energy values). Do not answer personal matrix/DOB from
    Knowledge or Memory alone. After you get an energy number, call knowledge_search for
    its meaning when the user wants interpretation.

    Do not pass a user id — the system injects it.
    """
    try:
        return user_context_service.get_context(user_id)
    except Exception as exc:
        return {"error": f"User context lookup failed: {exc}"}
