"""
Memory extractor
================
Turns a user message into structured long-term memories.

Uses the LLM + MEMORY_EXTRACTION_PROMPT.
Returns a list of memory dicts ready to save.
"""

import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.prompts.memory_prompt import MEMORY_EXTRACTION_PROMPT
from app.services.llm import llm


def _strip_code_fences(text: str) -> str:
    """LLMs sometimes wrap JSON in ```json ... ``` — remove that."""
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def _normalize_memories(payload: dict) -> list[dict]:
    """
    Accept both:
      - new format: { should_save, memories: [ {...}, ... ] }
      - old format: { should_save, category, memory_key, ... }  (single fact)

    Return a clean list of memory dicts (may be empty).
    """
    if not payload or not payload.get("should_save"):
        return []

    memories = payload.get("memories")

    # Old single-object format (backward compatible)
    if memories is None and payload.get("memory_key"):
        memories = [
            {
                "category": payload.get("category") or "other",
                "memory_key": payload.get("memory_key"),
                "memory_value": payload.get("memory_value") or "",
                "memory_text": payload.get("memory_text") or "",
                "importance": payload.get("importance") or 3,
            }
        ]

    if not isinstance(memories, list):
        return []

    cleaned: list[dict] = []
    for item in memories:
        if not isinstance(item, dict):
            continue

        key = str(item.get("memory_key") or "").strip()
        text = str(item.get("memory_text") or "").strip()
        value = str(item.get("memory_value") or "").strip()

        # Skip incomplete or empty facts
        if not key or not text:
            continue

        # Skip obvious meta / useless texts
        bad_phrases = (
            "person in conversation",
            "mentioned that the name",
            "talked about",
            "was discussed",
            "user clarified",
        )
        lower_text = text.lower()
        if any(phrase in lower_text for phrase in bad_phrases):
            continue

        try:
            importance = int(item.get("importance") or 3)
        except (TypeError, ValueError):
            importance = 3

        cleaned.append(
            {
                "category": str(item.get("category") or "other").strip(),
                "memory_key": key,
                "memory_value": value or text,
                "memory_text": text,
                "importance": max(1, min(importance, 5)),
            }
        )

    return cleaned


def extract_memories(
    user_message: str,
    recent_assistant_message: str | None = None,
) -> list[dict]:
    """
    Extract zero or more memories from the user's latest message.

    recent_assistant_message:
      Optional previous assistant reply. Helps when the user says
      "yes" / "he is my uncle" after a clarifying question.
    """
    if not (user_message or "").strip():
        return []

    human_parts = [f"User message:\n{user_message.strip()}"]

    if recent_assistant_message and recent_assistant_message.strip():
        human_parts.insert(
            0,
            f"Recent assistant message (context only):\n"
            f"{recent_assistant_message.strip()}",
        )

    response = llm.invoke(
        [
            SystemMessage(content=MEMORY_EXTRACTION_PROMPT),
            HumanMessage(content="\n\n".join(human_parts)),
        ]
    )

    raw = _strip_code_fences(getattr(response, "content", "") or "")

    try:
        payload = json.loads(raw)
    except Exception:
        return []

    if not isinstance(payload, dict):
        return []

    return _normalize_memories(payload)


def extract_memory(user_message: str):
    """
    Backward-compatible helper used by older call sites.

    Returns the first memory as a single dict with should_save,
    or { "should_save": False } when nothing was found.
    """
    memories = extract_memories(user_message)

    if not memories:
        return {"should_save": False}

    first = memories[0]
    return {
        "should_save": True,
        **first,
        "memories": memories,
    }
