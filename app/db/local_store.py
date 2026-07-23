"""In-memory fallbacks when Supabase is unreachable on the local machine."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from uuid import uuid4


class LocalDevStore:
    def __init__(self) -> None:
        self._messages: dict[tuple[str, str], list[dict]] = defaultdict(list)
        self._memories: dict[str, list[dict]] = defaultdict(list)

    def get_history(self, thread_id: str, user_id: str) -> list[dict]:
        return list(self._messages.get((thread_id, user_id), []))

    def save_message(
        self,
        thread_id: str,
        user_id: str,
        role: str,
        content: str,
    ) -> None:
        self._messages[(thread_id, user_id)].append(
            {
                "id": str(uuid4()),
                "thread_id": thread_id,
                "user_id": user_id,
                "role": role,
                "content": content,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    def list_threads(self, user_id: str) -> list[dict]:
        threads: dict[str, dict] = {}
        for (thread_id, owner_id), messages in self._messages.items():
            if owner_id != user_id or not messages:
                continue
            last = messages[-1]
            threads[thread_id] = {
                "thread_id": thread_id,
                "preview": (last.get("content") or "")[:120],
                "message_count": len(messages),
                "updated_at": last.get("created_at"),
            }
        return list(threads.values())

    def save_memory(
        self,
        user_id: str,
        category: str,
        key: str,
        value: str,
        memory_text: str,
        importance: int = 3,
    ) -> None:
        self._memories[user_id].append(
            {
                "category": category,
                "memory_key": key,
                "memory_value": value,
                "memory_text": memory_text,
                "importance": importance,
            }
        )

    def search_memories(self, user_id: str) -> list[dict]:
        return list(self._memories.get(user_id, []))

    def get_user_context(self, user_id: str) -> dict:
        return {
            "profile": {
                "id": user_id,
                "name": "Local Dev User",
            },
            "subscription": {
                "plan": "dev",
                "status": "active",
            },
            "personal_matrix": {},
            "metadata": {
                "source": "local_dev_mode",
            },
        }

    def search_knowledge(self, query: str) -> list[dict]:
        return [
            {
                "content": (
                    "Local dev mode is active. Supabase knowledge search is unavailable "
                    f"on this machine. Query was: {query}"
                ),
                "summary": "Local dev placeholder knowledge",
                "metadata": {"filename": "local-dev-mode"},
                "similarity": 1.0,
            }
        ]


local_dev_store = LocalDevStore()
