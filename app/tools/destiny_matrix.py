"""
LangChain tool: calculate_destiny_matrix
========================================

  - personal → calculate + save to saved_matrices (user only)
  - friend   → calculate + save name/DOB/matrix to long-term memory

After this tool returns energy numbers, call knowledge_search for meanings.
"""

from typing import Annotated

from langchain.tools import tool
from langgraph.prebuilt import InjectedState

from app.services.matrix_service import matrix_service


@tool
def calculate_destiny_matrix(
    date_of_birth: str,
    person_name: str = "",
    matrix_type: str = "friend",
    user_id: Annotated[str, InjectedState("user_id")] = "",
):
    """
    Calculate a Destiny Matrix from a date of birth and store it correctly.

    Storage rules:
    - matrix_type="personal" → save ONLY to saved_matrices (this user)
    - matrix_type="friend" → save to long-term memory as person facts
      (e.g. person_sarah_relation, person_sarah_dob, person_sarah_matrix)
      Never put friend/relative matrices into saved_matrices.

    Use when:
    - A friend/other person's DOB is known and you need their matrix numbers
    - get_user_context shows has_personal_matrix=false but profile.dob exists
      (pass that DOB with matrix_type="personal")

    Do NOT recalculate the user's own matrix if get_user_context already
    returned current_personal_matrix.

    For a friend already in memory (DOB or matrix), prefer memory_search first;
    only calculate again when needed.

    Args:
        date_of_birth: Birth date (DD/MM/YYYY, YYYY-MM-DD, or "11 July 1998").
        person_name: Required for friends (e.g. "Sarah") so memory keys match.
        matrix_type: "friend" (default) or "personal".

    Returns:
        JSON with date_of_birth, matrix values, and where it was stored.
        Then call knowledge_search to explain key energies.

    Do not pass user_id — the system injects it.
    """
    if not user_id:
        return {"error": "User id is required to store the matrix"}

    if not date_of_birth or not str(date_of_birth).strip():
        return {"error": "date_of_birth is required"}

    clean_type = (matrix_type or "friend").strip().lower()
    if clean_type == "friend" and not (person_name or "").strip():
        return {
            "error": "person_name is required for friend matrices "
            "(needed to save memory keys like person_sarah_matrix)."
        }

    try:
        return matrix_service.calculate_and_store(
            user_id=user_id,
            date_of_birth=str(date_of_birth).strip(),
            person_name=person_name or "",
            matrix_type=clean_type or "friend",
        )
    except (TypeError, ValueError) as exc:
        return {
            "error": str(exc),
            "hint": (
                "Use a clear date such as DD/MM/YYYY, YYYY-MM-DD, "
                "or 11 July 1998."
            ),
        }
    except Exception as exc:
        return {"error": f"Destiny Matrix calculation failed: {exc}"}
