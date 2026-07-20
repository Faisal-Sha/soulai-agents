"""
LangChain tools for Destiny Matrix calculations
===============================================

1) calculate_destiny_matrix  — one person (personal or friend)
2) calculate_compatibility_matrix — two people (HIL may collect DOBs first)
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


@tool
def calculate_compatibility_matrix(
    first_dob: str,
    second_dob: str,
    first_name: str = "",
    second_name: str = "",
    user_id: Annotated[str, InjectedState("user_id")] = "",
):
    """
    Calculate a Destiny Matrix compatibility reading for TWO people.

    Use when the user asks for compatibility / relationship matrix between
    two people (e.g. "me and Sarah", "Ali and Sara").

    Both dates of birth are REQUIRED. If either DOB is missing:
    - Ask ONE clear follow-up question (HIL will resume later)
    - Do not invent DOBs
    - For "me / my" as one person: call get_user_context first and use
      profile.dob or the personal matrix birth_date as first_dob

    Prefer memory_search first if a previous compat_* memory already exists.

    Args:
        first_dob: First person's birth date (DD/MM/YYYY, YYYY-MM-DD, or
            natural form like "4 December 2009").
        second_dob: Second person's birth date.
        first_name: Optional label (e.g. "me", "Ali").
        second_name: Optional label (e.g. "Sarah").

    Returns:
        compatibility_matrix (full energy map), compatibility_summary
        (pair_center, relationship_energy, harmony_area, challenge_area, ...),
        and memory save metadata.
        Then call knowledge_search for 1–2 key energy meanings.

    Do not pass user_id — the system injects it.
    """
    if not user_id:
        return {"error": "User id is required to store the compatibility reading"}

    if not first_dob or not str(first_dob).strip():
        return {"error": "first_dob is required"}

    if not second_dob or not str(second_dob).strip():
        return {"error": "second_dob is required"}

    try:
        return matrix_service.calculate_compatibility(
            user_id=user_id,
            first_dob=str(first_dob).strip(),
            second_dob=str(second_dob).strip(),
            first_name=first_name or "",
            second_name=second_name or "",
        )
    except (TypeError, ValueError) as exc:
        return {
            "error": str(exc),
            "hint": (
                "Use clear dates such as DD/MM/YYYY, YYYY-MM-DD, "
                "or 11 July 1998 for both people."
            ),
        }
    except Exception as exc:
        return {
            "error": f"Compatibility matrix calculation failed: {exc}"
        }
