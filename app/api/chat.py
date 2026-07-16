"""
Chat API — the real orchestrator
================================

Flow (easy mental model):

  User message
       │
       ▼
  Load chat history (Supabase)
       │
       ▼
  Load conversation_context (pending task?)
       │
       ├── YES, waiting  → fill slots from user reply
       │                      ├── still missing → ask again (no graph)
       │                      └── all filled    → resume message → graph
       │
       └── NO pending    → normal graph invoke
                              │
                              ▼
                         Save chat history
                         Extract long-term memory
                         Clarification service.check()
                              │
                              └── if needs follow-up → save conversation_context

LangGraph never stores "waiting for DOB".
That lives in conversation_context (database).
"""

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

# Memory (long-term facts about the user)
from app.memory.memory_extractor import extract_memories
from app.services.memory_service import memory_service

# Chat History (full messages for a thread)
from app.services.chat_history_service import chat_history_service

# Temporary multi-turn work (e.g. waiting for friend's DOB)
from app.services.conversation_context_service import (
    conversation_context_service,
)
from app.services.clarification_service import clarification_service


logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# Small helpers (keep /chat readable)
# =============================================================================

def _last_assistant_text(history: list) -> str | None:
    """Find the most recent assistant message (helps memory extraction)."""
    for item in reversed(history or []):
        if item.get("role") == "assistant" and item.get("content"):
            return item["content"]
    return None


def _persist_memory(
    user_id: str,
    message: str,
    recent_assistant_message: str | None = None,
) -> None:
    """
    Best-effort long-term memory; never fail the chat response.

    Can save MULTIPLE facts from one message, e.g.:
      "Ali is my uncle, DOB 11 July 1998"
      → person_ali_relation + person_ali_dob
    """
    try:
        memories = extract_memories(
            user_message=message,
            recent_assistant_message=recent_assistant_message,
        )

        for memory in memories:
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


def _save_turn(
    thread_id: str,
    user_id: str,
    user_message: str,
    assistant_answer: str,
) -> None:
    """Save both sides of one chat turn to Supabase."""
    chat_history_service.save_message(
        thread_id=thread_id,
        user_id=user_id,
        role="user",
        content=user_message,
    )
    chat_history_service.save_message(
        thread_id=thread_id,
        user_id=user_id,
        role="assistant",
        content=assistant_answer,
    )


def _run_graph(
    *,
    messages: list,
    user_language: str,
    user_id: str,
    thread_id: str,
) -> str:
    """
    Call LangGraph once and return the assistant text.

    The graph only receives messages + language + user_id.
    It does NOT receive pending/clarification state.
    """
    result = graph.invoke(
        {
            "messages": messages,
            "user_language": user_language,
            "user_id": user_id,
        },
        config={
            "configurable": {
                "thread_id": thread_id,
            }
        },
    )

    ai_message = result["messages"][-1]
    return ai_message.content or "I could not generate a response."


def _pending_snapshot(pending: dict | None) -> dict | None:
    """Small dict for the API response (easy to debug in Postman / frontend)."""
    if not pending:
        return None

    return {
        "intent": pending.get("intent"),
        "status": pending.get("status"),
        "slots": pending.get("slots"),
    }


# =============================================================================
# Endpoints
# =============================================================================

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
    """
    Main chat turn.

    Read the comments inside — this function is the "conductor"
    that decides whether to resume a pending task or start a normal turn.
    """
    try:
        user_language = detect_user_language(request.message)

        # ------------------------------------------------------------------
        # 1) Load previous messages for this thread
        # ------------------------------------------------------------------
        history = chat_history_service.get_history(
            thread_id=request.thread_id,
            user_id=request.user_id,
        )
        messages = chat_history_service.to_langchain_messages(history)

        # ------------------------------------------------------------------
        # 2) Load temporary pending work (if any)
        # ------------------------------------------------------------------
        pending = conversation_context_service.get(
            thread_id=request.thread_id,
            user_id=request.user_id,
        )

        answer: str
        response_status = "complete"
        response_pending: dict | None = None

        # ==================================================================
        # PATH A — We were waiting for the user (e.g. friend's DOB)
        # ==================================================================
        if pending and pending.get("status") == "waiting":

            # User started a totally new question? Drop pending and go normal.
            if clarification_service.looks_like_new_request(request.message):
                conversation_context_service.clear(
                    thread_id=request.thread_id,
                    user_id=request.user_id,
                )
                pending = None
                # Fall through to PATH B below (normal turn)

            else:
                # Fill the missing slot(s) from this reply
                updated = clarification_service.fill_from_user_message(
                    pending,
                    request.message,
                )

                # Still missing info → ask again (do NOT call the graph)
                if not clarification_service.is_ready(updated):
                    conversation_context_service.upsert(
                        thread_id=request.thread_id,
                        user_id=request.user_id,
                        status="waiting",
                        intent=updated["intent"],
                        slots=updated["slots"],
                    )

                    answer = clarification_service.build_followup_question(
                        updated
                    )

                    _save_turn(
                        request.thread_id,
                        request.user_id,
                        request.message,
                        answer,
                    )
                    # Do not extract long-term memory from a short DOB reply

                    return ChatResponse(
                        answer=answer,
                        sources=[],
                        status="waiting",
                        pending=_pending_snapshot(updated),
                    )

                # All slots filled → clear pending, then resume via the graph
                conversation_context_service.clear(
                    thread_id=request.thread_id,
                    user_id=request.user_id,
                )

                resume_text = clarification_service.build_resume_message(
                    updated
                )

                # History still stores what the user actually typed
                # Graph gets a clearer "resume" instruction
                messages.append(HumanMessage(content=resume_text))

                answer = _run_graph(
                    messages=messages,
                    user_language=user_language,
                    user_id=request.user_id,
                    thread_id=request.thread_id,
                )

                _save_turn(
                    request.thread_id,
                    request.user_id,
                    request.message,
                    answer,
                )
                # Resume replies are often just a DOB — skip weak one-line memory saves
                # unless the message clearly contains a relationship/personal fact.
                _persist_memory(
                    request.user_id,
                    request.message,
                    recent_assistant_message=_last_assistant_text(history),
                )

                return ChatResponse(
                    answer=answer,
                    sources=[],
                    status="complete",
                    pending=None,
                )

        # ==================================================================
        # PATH B — Normal turn (no pending wait)
        # ==================================================================
        messages.append(HumanMessage(content=request.message))

        answer = _run_graph(
            messages=messages,
            user_language=user_language,
            user_id=request.user_id,
            thread_id=request.thread_id,
        )

        _save_turn(
            request.thread_id,
            request.user_id,
            request.message,
            answer,
        )
        # Pass previous assistant reply so "yes, he is my uncle" can become a clear fact
        _persist_memory(
            request.user_id,
            request.message,
            recent_assistant_message=_last_assistant_text(history),
        )

        # ------------------------------------------------------------------
        # 3) After the reply: should we wait for clarification next turn?
        # ------------------------------------------------------------------
        new_pending = clarification_service.check(
            user_message=request.message,
            assistant_answer=answer,
        )

        if new_pending:
            conversation_context_service.upsert(
                thread_id=request.thread_id,
                user_id=request.user_id,
                status=new_pending["status"],
                intent=new_pending["intent"],
                slots=new_pending["slots"],
            )
            response_status = "waiting"
            response_pending = _pending_snapshot(new_pending)

        return ChatResponse(
            answer=answer,
            sources=[],
            status=response_status,
            pending=response_pending,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )
