from langchain.tools import tool

from app.services.knowledge import knowledge_service


@tool
def knowledge_search(question: str):
    """
    Search the SoulPlus knowledge base for concepts, energy meanings, and spiritual theory.

    Use for:
    - General questions (no "my"): Matrix of Destiny, numerology, energy meanings,
      compatibility theory, Human Design, astrology, spiritual concepts.
    - AFTER get_user_context or calculate_destiny_matrix: explain a personal energy
      (e.g. question="Matrix of Destiny energy 9 meaning and interpretation").

    Do NOT use this alone for the user's own DOB, matrix numbers, or subscription —
    call get_user_context (or calculate_destiny_matrix if no saved matrix) for those first.

    Pass a clear natural-language search question focused on the concept to retrieve.
    """
    try:
        documents = knowledge_service.search(question) or []
    except Exception as exc:
        return [{"error": f"Knowledge search failed: {exc}"}]

    return [
        {
            "content": doc.get("content"),
            "summary": doc.get("summary"),
            "source": (doc.get("metadata") or {}).get("filename"),
            "similarity": doc.get("similarity"),
        }
        for doc in documents
    ]
