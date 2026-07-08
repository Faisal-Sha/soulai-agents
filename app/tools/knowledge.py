from langchain.tools import tool

from app.services.knowledge import knowledge_service


@tool
def knowledge_search(question: str):
    """
    Search the SoulPlus knowledge base.
    Returns the most relevant document chunks.
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
