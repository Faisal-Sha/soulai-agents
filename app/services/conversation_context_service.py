"""
Conversation Context Service
============================

Talks to Supabase about TEMPORARY multi-turn work.

Think of it as a sticky note on a chat thread:

    "We asked for Asim's DOB. Still waiting."

Long-term facts go to Memory Service.
Full messages go to Chat History Service.
This service only stores the current unfinished task.
"""

import json

from app.db.supabase import supabase


class ConversationContextService:
    """Simple CRUD helpers for the conversation_context table."""

    def get(
        self,
        thread_id: str,
        user_id: str,
    ) -> dict | None:
        """
        Load the active pending context for this thread.

        Returns None when there is nothing waiting.
        Returns a dict like:
        {
            "thread_id": "...",
            "status": "waiting",
            "intent": "friend_matrix",
            "slots": {"friend_name": "Asim", "friend_dob": None},
            ...
        }
        """
        response = supabase.rpc(
            "get_conversation_context",
            {
                "p_thread_id": thread_id,
                "p_user_id": user_id,
            },
        ).execute()

        rows = response.data or []

        if not rows:
            return None

        # RPC returns a list; we only keep one row per thread
        row = rows[0]

        # Supabase may return slots already as a dict (jsonb)
        slots = row.get("slots") or {}
        if isinstance(slots, str):
            # Safety: if it ever comes back as a JSON string, parse it
            slots = json.loads(slots)

        return {
            "id": row.get("id"),
            "thread_id": row.get("thread_id"),
            "user_id": str(row.get("user_id")),
            "status": row.get("status"),
            "intent": row.get("intent"),
            "slots": slots,
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at"),
        }

    def upsert(
        self,
        thread_id: str,
        user_id: str,
        status: str,
        intent: str,
        slots: dict,
    ) -> None:
        """
        Create or update the pending context for this thread.

        status examples: "waiting", "ready", "cleared"
        intent example:  "friend_matrix"
        slots example:   {"friend_name": "Asim", "friend_dob": None}
        """
        supabase.rpc(
            "upsert_conversation_context",
            {
                "p_thread_id": thread_id,
                "p_user_id": user_id,
                "p_status": status,
                "p_intent": intent,
                "p_slots": slots,
            },
        ).execute()

    def clear(
        self,
        thread_id: str,
        user_id: str,
    ) -> None:
        """Delete pending context when the task is finished or cancelled."""
        supabase.rpc(
            "clear_conversation_context",
            {
                "p_thread_id": thread_id,
                "p_user_id": user_id,
            },
        ).execute()


# One shared instance used by the chat endpoint
conversation_context_service = ConversationContextService()
