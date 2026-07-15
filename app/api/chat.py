import logging

from fastapi import APIRouter, HTTPException, Query
from langchain_core.messages import HumanMessage

from app.graph.graph import graph
from app.schemas import (
    ChatHistoryMessage,
    ChatRequest,
    ChatResponse,
    ChatThreadSummary,
)

from app.services.language import detect_user_language

# Memory
from app.memory.memory_extractor import extract_memory
from app.services.memory_service import memory_service

# Chat History
from app.services.chat_history_service import chat_history_service


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
        logger.exception(
            "Failed to persist memory for user_id=%s",
            user_id,
        )


@router.get("/chat/threads", response_model=list[ChatThreadSummary])
def list_threads(user_id: str = Query(...)):
    try:
        return chat_history_service.list_threads(user_id=user_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/chat/history", response_model=list[ChatHistoryMessage])
def get_history(
    user_id: str = Query(...),
    thread_id: str = Query(...),
):
    try:
        return chat_history_service.get_history(
            thread_id=thread_id,
            user_id=user_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    try:

        user_language = detect_user_language(
            request.message
        )

        # -------------------------------------------------
        # Load previous conversation
        # -------------------------------------------------

        history = chat_history_service.get_history(
            thread_id=request.thread_id,
            user_id=request.user_id,
        )

        messages = chat_history_service.to_langchain_messages(
            history
        )

        # Add current user message (NOT yet saved to DB)
        messages.append(
            HumanMessage(
                content=request.message
            )
        )

        # -------------------------------------------------
        # Invoke LangGraph
        # -------------------------------------------------

        result = graph.invoke(
            {
                "messages": messages,
                "user_language": user_language,
                "user_id": request.user_id,
            },
            config={
                "configurable": {
                    "thread_id": request.thread_id,
                }
            },
        )

        ai_message = result["messages"][-1]

        answer = (
            ai_message.content
            or "I could not generate a response."
        )

        # -------------------------------------------------
        # Save conversation
        # -------------------------------------------------

        chat_history_service.save_message(
            thread_id=request.thread_id,
            user_id=request.user_id,
            role="user",
            content=request.message,
        )

        chat_history_service.save_message(
            thread_id=request.thread_id,
            user_id=request.user_id,
            role="assistant",
            content=answer,
        )

        # -------------------------------------------------
        # Persist long-term memory
        # -------------------------------------------------

        _persist_memory(
            request.user_id,
            request.message,
        )

        return ChatResponse(
            answer=answer,
            sources=[],
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )