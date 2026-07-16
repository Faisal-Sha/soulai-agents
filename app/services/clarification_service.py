"""
Clarification Service
=====================

Business logic for "ask a follow-up question, then resume later".

This is NOT a LangGraph node.
The graph only talks to the LLM + tools.
This service decides:

  1) Do we need to wait for more info?     → check()
  2) Did the user just answer a missing slot? → fill_from_user_message()
  3) Are all slots filled so we can resume? → is_ready()
  4) What message should we send the graph? → build_resume_message()

Start simple (rules / keywords). Later you can swap parts for an LLM
without changing the chat endpoint much.
"""

from __future__ import annotations

import re
from copy import deepcopy


class ClarificationService:
    """
    Beginner-friendly helpers for pending multi-turn tasks.

    First supported intent: friend_matrix
    Required slots: friend_name, friend_dob
    """

    # -------------------------------------------------------------------------
    # Public API used by /chat
    # -------------------------------------------------------------------------

    def check(
        self,
        user_message: str,
        assistant_answer: str,
    ) -> dict | None:
        """
        After a normal graph reply, decide if we should store a pending task.

        Returns a pending dict, or None if nothing to wait for.

        Example return value:
        {
            "intent": "friend_matrix",
            "status": "waiting",
            "slots": {
                "friend_name": "Asim",
                "friend_dob": None,
            },
        }
        """
        # For now we only handle one workflow: friend Destiny Matrix
        if not self._looks_like_friend_matrix_request(user_message):
            return None

        # Only create pending state if the assistant actually asked for DOB
        if not self._assistant_asked_for_dob(assistant_answer):
            return None

        friend_name = self._extract_friend_name(user_message)

        return {
            "intent": "friend_matrix",
            "status": "waiting",
            "slots": {
                "friend_name": friend_name,
                "friend_dob": None,
            },
        }

    def fill_from_user_message(
        self,
        pending: dict,
        user_message: str,
    ) -> dict:
        """
        Take the user's reply and fill the first empty slot we are waiting for.

        Example:
          pending slots = {friend_name: "Asim", friend_dob: None}
          user says     = "11 July 1998"
          result slots  = {friend_name: "Asim", friend_dob: "11 July 1998"}
        """
        updated = deepcopy(pending)
        slots = dict(updated.get("slots") or {})
        reply = (user_message or "").strip()

        missing_field = self.get_first_missing_slot(slots)

        if missing_field is None:
            # Nothing missing — mark ready
            updated["slots"] = slots
            updated["status"] = "ready"
            return updated

        # Special case:
        # We still need friend_name, but the user sent a date.
        # Example: name extract failed earlier, user replies "11 July 1998".
        # Fill friend_dob instead of putting the date into friend_name.
        if (
            missing_field == "friend_name"
            and self._looks_like_date(reply)
            and "friend_dob" in slots
        ):
            slots["friend_dob"] = reply
        else:
            # Normal case: fill whatever slot we are waiting for
            slots[missing_field] = reply

        updated["slots"] = slots

        if self.get_first_missing_slot(slots) is None:
            updated["status"] = "ready"
        else:
            updated["status"] = "waiting"

        return updated

    def is_ready(self, pending: dict) -> bool:
        """True when every required slot has a non-empty value."""
        slots = pending.get("slots") or {}
        return self.get_first_missing_slot(slots) is None

    def get_first_missing_slot(self, slots: dict) -> str | None:
        """
        Return the name of the first empty slot, or None if all filled.

        Empty means: missing key, None, or blank string.
        """
        # Order matters: ask for name before DOB if both are empty
        required_order = ["friend_name", "friend_dob"]

        for field in required_order:
            if field not in slots:
                # Only require fields that exist for this intent's slot schema
                continue
            value = slots.get(field)
            if value is None or str(value).strip() == "":
                return field

        return None

    def build_followup_question(self, pending: dict) -> str:
        """
        Build a short question when we still need information
        (used if the user replied but the slot is still empty / unclear).
        """
        slots = pending.get("slots") or {}
        intent = pending.get("intent")
        missing = self.get_first_missing_slot(slots)

        if intent == "friend_matrix" and missing == "friend_dob":
            name = slots.get("friend_name") or "your friend"
            return f"What is {name}'s date of birth? (for example: 11 July 1998)"

        if intent == "friend_matrix" and missing == "friend_name":
            return "What is your friend's name?"

        return "Could you share a bit more detail so I can continue?"

    def build_resume_message(self, pending: dict) -> str:
        """
        Build a clear instruction for the graph after all slots are filled.

        The graph itself does not know about conversation_context.
        We pass everything it needs inside this one user-facing message.
        """
        intent = pending.get("intent")
        slots = pending.get("slots") or {}

        if intent == "friend_matrix":
            name = slots.get("friend_name") or "the friend"
            dob = slots.get("friend_dob") or "unknown"

            return (
                f"Please continue the earlier request about {name}'s Destiny Matrix.\n"
                f"Friend name: {name}\n"
                f"Friend date of birth: {dob}\n"
                f"Use this information to give a helpful Destiny Matrix reading for {name}. "
                f"Do not ask for the date of birth again."
            )

        # Fallback for future intents
        return (
            "Please continue the pending task with this information:\n"
            f"Intent: {intent}\n"
            f"Slots: {slots}"
        )

    def looks_like_new_request(self, user_message: str) -> bool:
        """
        Rough check: is the user starting a brand new question
        instead of answering our follow-up?

        If yes, /chat should clear pending and run a normal graph turn.
        """
        text = (user_message or "").strip()

        # Short replies (dates, "Asim", "yes") are usually slot answers
        if len(text) < 40 and not text.endswith("?"):
            return False

        # Longer questions / new topics → treat as a new request
        new_request_hints = [
            "what is",
            "what's",
            "tell me",
            "explain",
            "my matrix",
            "my dob",
            "remember",
            "who is",
            "how do",
        ]
        lower = text.lower()
        return any(hint in lower for hint in new_request_hints) or text.endswith("?")

    # -------------------------------------------------------------------------
    # Private helpers (simple keyword rules — easy to read and change)
    # -------------------------------------------------------------------------

    def _looks_like_friend_matrix_request(self, message: str) -> bool:
        """Detect requests like: Read Asim's matrix / friend's destiny matrix."""
        lower = (message or "").lower()

        mentions_matrix = any(
            word in lower
            for word in ("matrix", "destiny matrix", "friend matrix")
        )
        mentions_friend = any(
            word in lower
            for word in ("friend", "'s matrix", "for ")
        )
        # Also: "read asim's matrix" — has matrix + a name-like pattern
        has_name_possessive = bool(
            re.search(r"\b[A-Za-z]{2,}'s\s+matrix\b", message or "", re.I)
        )

        return mentions_matrix and (mentions_friend or has_name_possessive)

    def _assistant_asked_for_dob(self, answer: str) -> bool:
        """Detect that the assistant asked for a date of birth."""
        lower = (answer or "").lower()
        dob_phrases = [
            "date of birth",
            "date ofbirth",
            "birth date",
            "birthday",
            "when was",
            "born",
            "dob",
            "year of birth",
        ]
        return any(phrase in lower for phrase in dob_phrases)

    def _extract_friend_name(self, message: str) -> str | None:
        """
        Try to pull a friend name from the user message.

        Examples it understands:
          - "Read Asim's matrix"
          - "friend matrix for Asim"
          - "Asim destiny matrix"
        """
        text = (message or "").strip()

        # Pattern 1: Name's matrix
        match = re.search(
            r"\b([A-Za-z]{2,})'s\s+(?:destiny\s+)?matrix\b",
            text,
            re.I,
        )
        if match:
            return match.group(1).capitalize()

        # Pattern 2: for Name
        match = re.search(
            r"\bfor\s+([A-Za-z]{2,})\b",
            text,
            re.I,
        )
        if match:
            return match.group(1).capitalize()

        # Pattern 3: friend Name
        match = re.search(
            r"\bfriend\s+([A-Za-z]{2,})\b",
            text,
            re.I,
        )
        if match:
            return match.group(1).capitalize()

        return None

    def _looks_like_date(self, message: str) -> bool:
        """
        Very simple date detector for beginner code.

        Accepts things like:
          - 11 July 1998
          - 11/07/1998
          - 1998-07-11
          - July 11, 1998
        """
        text = (message or "").strip()
        if not text:
            return False

        # Has a 4-digit year somewhere
        has_year = bool(re.search(r"\b(19|20)\d{2}\b", text))

        # Has digits (day/month) or a month name
        month_names = (
            "january", "february", "march", "april", "may", "june",
            "july", "august", "september", "october", "november", "december",
            "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "oct",
            "nov", "dec",
        )
        lower = text.lower()
        has_month_name = any(m in lower for m in month_names)
        has_digits = bool(re.search(r"\d", text))

        return has_year and (has_month_name or has_digits)


# One shared instance used by the chat endpoint
clarification_service = ClarificationService()
