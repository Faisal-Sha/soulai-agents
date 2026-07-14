import logging

from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage

from app.graph.graph import graph
from app.schemas import ChatRequest, ChatResponse
from app.services.language import detect_user_language

# Memory
from app.memory.memory_extractor import extract_memory
from app.services.memory_service import memory_service

logger = logging.getLogger(__name__)
router = APIRouter()


def _persist_memory(user_id: str, message: str) -> None:
    """Best-effort long-term memory; never fail the chat response."""
    try:
        memory = extract_memory(message)
        if not memory.get("should_save"):
            return

        memory_service.save_memory(
            user_id=user_id,
            category=memory["category"],
            key=memory["memory_key"],
            value=memory["memory_value"],
            memory_text=memory["memory_text"],
            importance=memory["importance"],
        )
    except Exception:
        logger.exception("Failed to persist memory for user_id=%s", user_id)


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        user_language = detect_user_language(request.message)

        result = graph.invoke(
            {
                "messages": [
                    HumanMessage(content=request.message)
                ],
                "user_language": user_language,
                "user_id": request.user_id,
            },
            config={
                "configurable": {
                    "thread_id": request.thread_id,
                }
            }
        )

        ai_message = result["messages"][-1]
        answer = ai_message.content or "I could not generate a response."

        _persist_memory(request.user_id, request.message)

        return ChatResponse(
            answer=answer,
            sources=[],
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )