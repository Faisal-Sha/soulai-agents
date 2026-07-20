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

Supported intents:
  - friend_matrix         slots: friend_name, friend_dob
  - compatibility_matrix  slots: with_user, person_a_name, person_a_dob,
                                 person_b_name, person_b_dob
"""

from __future__ import annotations

import re
from copy import deepcopy


class ClarificationService:
    """Beginner-friendly helpers for pending multi-turn tasks."""

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
        """
        # Compatibility first — "compatibility with Sarah" is not a friend matrix
        if self._looks_like_compatibility_request(user_message):
            if not self._assistant_asked_for_dob(assistant_answer):
                return None
            return self._build_compatibility_pending(user_message)

        if self._looks_like_friend_matrix_request(user_message):
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

        return None

    def fill_from_user_message(
        self,
        pending: dict,
        user_message: str,
    ) -> dict:
        """Fill the first empty slot from the user's reply."""
        updated = deepcopy(pending)
        slots = dict(updated.get("slots") or {})
        reply = (user_message or "").strip()
        intent = updated.get("intent")

        missing_field = self.get_first_missing_slot(slots, intent=intent)

        if missing_field is None:
            updated["slots"] = slots
            updated["status"] = "ready"
            return updated

        # If we need a name but the user sent a date, fill the matching DOB slot
        if (
            missing_field.endswith("_name")
            and self._looks_like_date(reply)
        ):
            dob_field = missing_field.replace("_name", "_dob")
            if dob_field in slots:
                slots[dob_field] = reply
            else:
                slots[missing_field] = reply
        else:
            slots[missing_field] = reply

        updated["slots"] = slots

        if self.get_first_missing_slot(slots, intent=intent) is None:
            updated["status"] = "ready"
        else:
            updated["status"] = "waiting"

        return updated

    def is_ready(self, pending: dict) -> bool:
        """True when every required slot has a non-empty value."""
        slots = pending.get("slots") or {}
        intent = pending.get("intent")
        return self.get_first_missing_slot(slots, intent=intent) is None

    def get_first_missing_slot(
        self,
        slots: dict,
        intent: str | None = None,
    ) -> str | None:
        """
        Return the name of the first empty slot, or None if all filled.
        """
        if intent == "compatibility_matrix":
            with_user = bool(slots.get("with_user"))
            if with_user:
                # User DOB comes from get_user_context on resume
                required_order = ["person_b_name", "person_b_dob"]
            else:
                required_order = [
                    "person_a_name",
                    "person_a_dob",
                    "person_b_name",
                    "person_b_dob",
                ]
        else:
            # friend_matrix (default)
            required_order = ["friend_name", "friend_dob"]

        for field in required_order:
            if field not in slots:
                continue
            value = slots.get(field)
            if value is None or str(value).strip() == "":
                return field

        return None

    def build_followup_question(self, pending: dict) -> str:
        """Short question when we still need information."""
        slots = pending.get("slots") or {}
        intent = pending.get("intent")
        missing = self.get_first_missing_slot(slots, intent=intent)

        if intent == "compatibility_matrix":
            if missing == "person_b_dob":
                name = slots.get("person_b_name") or "the other person"
                return (
                    f"What is {name}'s date of birth? "
                    f"(for example: 11 July 1998)"
                )
            if missing == "person_a_dob":
                name = slots.get("person_a_name") or "the first person"
                return (
                    f"What is {name}'s date of birth? "
                    f"(for example: 11 July 1998)"
                )
            if missing == "person_b_name":
                return "Who is the second person for the compatibility reading?"
            if missing == "person_a_name":
                return "Who is the first person for the compatibility reading?"

        if intent == "friend_matrix" and missing == "friend_dob":
            name = slots.get("friend_name") or "your friend"
            return f"What is {name}'s date of birth? (for example: 11 July 1998)"

        if intent == "friend_matrix" and missing == "friend_name":
            return "What is your friend's name?"

        return "Could you share a bit more detail so I can continue?"

    def build_resume_message(self, pending: dict) -> str:
        """Clear instruction for the graph after all slots are filled."""
        intent = pending.get("intent")
        slots = pending.get("slots") or {}

        if intent == "friend_matrix":
            name = slots.get("friend_name") or "the friend"
            dob = slots.get("friend_dob") or "unknown"

            return (
                f"Please continue the earlier request about {name}'s Destiny Matrix.\n"
                f"Friend name: {name}\n"
                f"Friend date of birth: {dob}\n"
                f"Steps:\n"
                f"1) Call calculate_destiny_matrix with date_of_birth=\"{dob}\", "
                f"person_name=\"{name}\", matrix_type=\"friend\".\n"
                f"   (This saves {name}'s relation, DOB, and matrix into long-term "
                f"memory — not saved_matrices.)\n"
                f"2) Call knowledge_search for the meaning of 1–2 key energies "
                f"(for example center or money).\n"
                f"3) Give a helpful Destiny Matrix reading for {name}.\n"
                f"Do not ask for the date of birth again. Do not invent matrix numbers."
            )

        if intent == "compatibility_matrix":
            with_user = bool(slots.get("with_user"))
            name_a = slots.get("person_a_name") or "Person A"
            name_b = slots.get("person_b_name") or "Person B"
            dob_a = slots.get("person_a_dob") or "unknown"
            dob_b = slots.get("person_b_dob") or "unknown"

            if with_user:
                return (
                    f"Please continue the earlier compatibility request between "
                    f"the user and {name_b}.\n"
                    f"Person A: the authenticated user (me)\n"
                    f"Person B: {name_b}\n"
                    f"Person B date of birth: {dob_b}\n"
                    f"Steps:\n"
                    f"1) Call get_user_context and read the user's DOB "
                    f"(profile.dob or current_personal_matrix.birth_date).\n"
                    f"2) Call calculate_compatibility_matrix with "
                    f"first_dob=<user DOB>, second_dob=\"{dob_b}\", "
                    f"first_name=\"me\", second_name=\"{name_b}\".\n"
                    f"3) Call knowledge_search for 1–2 key compatibility energies "
                    f"(for example pair_center or relationship_energy).\n"
                    f"4) Give a helpful compatibility reading.\n"
                    f"Do not ask for dates of birth again. Do not invent numbers."
                )

            return (
                f"Please continue the earlier compatibility request between "
                f"{name_a} and {name_b}.\n"
                f"Person A: {name_a}\n"
                f"Person A date of birth: {dob_a}\n"
                f"Person B: {name_b}\n"
                f"Person B date of birth: {dob_b}\n"
                f"Steps:\n"
                f"1) Call calculate_compatibility_matrix with "
                f"first_dob=\"{dob_a}\", second_dob=\"{dob_b}\", "
                f"first_name=\"{name_a}\", second_name=\"{name_b}\".\n"
                f"2) Call knowledge_search for 1–2 key compatibility energies.\n"
                f"3) Give a helpful compatibility reading.\n"
                f"Do not ask for dates of birth again. Do not invent numbers."
            )

        return (
            "Please continue the pending task with this information:\n"
            f"Intent: {intent}\n"
            f"Slots: {slots}"
        )

    def looks_like_new_request(self, user_message: str) -> bool:
        """
        Rough check: is the user starting a brand new question
        instead of answering our follow-up?
        """
        text = (user_message or "").strip()

        if len(text) < 40 and not text.endswith("?"):
            return False

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
            "compatibility",
        ]
        lower = text.lower()
        return any(hint in lower for hint in new_request_hints) or text.endswith("?")

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _build_compatibility_pending(self, user_message: str) -> dict:
        """
        Build pending slots for a compatibility request.

        Cases:
          - "my compatibility with Sarah" → with_user=True, wait for Sarah DOB
          - "compatibility between Ali and Sarah" → wait for both DOBs
        """
        with_user = self._compatibility_includes_user(user_message)
        names = self._extract_compatibility_names(user_message)

        if with_user:
            partner = None
            for name in names:
                if name.lower() not in ("me", "my", "i", "myself"):
                    partner = name
                    break

            return {
                "intent": "compatibility_matrix",
                "status": "waiting",
                "slots": {
                    "with_user": True,
                    "person_a_name": "me",
                    "person_a_dob": None,  # filled from get_user_context on resume
                    "person_b_name": partner,
                    "person_b_dob": None,
                },
            }

        name_a = names[0] if len(names) >= 1 else None
        name_b = names[1] if len(names) >= 2 else None

        return {
            "intent": "compatibility_matrix",
            "status": "waiting",
            "slots": {
                "with_user": False,
                "person_a_name": name_a,
                "person_a_dob": None,
                "person_b_name": name_b,
                "person_b_dob": None,
            },
        }

    def _looks_like_compatibility_request(self, message: str) -> bool:
        """Detect: compatibility with Sarah / relationship matrix / etc."""
        lower = (message or "").lower()
        return any(
            word in lower
            for word in (
                "compatibility",
                "compatible",
                "compatibility matrix",
                "relationship matrix",
                "match with",
                "compat with",
            )
        )

    def _compatibility_includes_user(self, message: str) -> bool:
        """True for 'my compatibility with X' / 'me and Sarah'."""
        lower = (message or "").lower()

        # Plain phrases that cannot false-match inside other names
        if any(
            phrase in lower
            for phrase in (
                "my compatibility",
                "compatibility with me",
                "between me",
                "with me",
                "myself and",
                "and myself",
            )
        ):
            return True

        # Word-boundary checks (avoid matching "i and" inside "Ali and")
        if re.search(r"\bme and\b", lower):
            return True
        if re.search(r"\band me\b", lower):
            return True
        if re.search(r"\bi and\b", lower):
            return True
        if re.search(r"\band i\b", lower):
            return True

        if re.search(r"\b(my|me|myself)\b.{0,40}\bcompatibil", lower):
            return True
        if re.search(r"\bcompatibil.{0,40}\b(my|me|myself)\b", lower):
            return True

        return False

    def _extract_compatibility_names(self, message: str) -> list[str]:
        """
        Pull person names from compatibility requests.

        Examples:
          - "compatibility with Sarah"
          - "compatibility between Ali and Sara"
          - "my compatibility with Sarah"
        """
        text = (message or "").strip()
        names: list[str] = []

        # between A and B
        match = re.search(
            r"\bbetween\s+([A-Za-z]{2,})\s+and\s+([A-Za-z]{2,})\b",
            text,
            re.I,
        )
        if match:
            return [match.group(1).capitalize(), match.group(2).capitalize()]

        # A and B compatibility / A and B matrix
        match = re.search(
            r"\b([A-Za-z]{2,})\s+and\s+([A-Za-z]{2,})\b",
            text,
            re.I,
        )
        if match:
            a, b = match.group(1), match.group(2)
            skip = {"my", "me", "i", "the", "our"}
            if a.lower() not in skip:
                names.append(a.capitalize())
            else:
                names.append("me")
            if b.lower() not in skip:
                names.append(b.capitalize())
            else:
                names.append("me")
            return names

        # with Name
        match = re.search(
            r"\bwith\s+([A-Za-z]{2,})\b",
            text,
            re.I,
        )
        if match and match.group(1).lower() not in ("me", "my", "i"):
            return [match.group(1).capitalize()]

        return names

    def _looks_like_friend_matrix_request(self, message: str) -> bool:
        """Detect requests like: Read Asim's matrix / friend's destiny matrix."""
        if self._looks_like_compatibility_request(message):
            return False

        lower = (message or "").lower()

        mentions_matrix = any(
            word in lower
            for word in ("matrix", "destiny matrix", "friend matrix")
        )
        mentions_friend = any(
            word in lower
            for word in ("friend", "'s matrix", "for ")
        )
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
        """Try to pull a friend name from the user message."""
        text = (message or "").strip()

        match = re.search(
            r"\b([A-Za-z]{2,})'s\s+(?:destiny\s+)?matrix\b",
            text,
            re.I,
        )
        if match:
            return match.group(1).capitalize()

        match = re.search(
            r"\bfor\s+([A-Za-z]{2,})\b",
            text,
            re.I,
        )
        if match:
            return match.group(1).capitalize()

        match = re.search(
            r"\bfriend\s+([A-Za-z]{2,})\b",
            text,
            re.I,
        )
        if match:
            return match.group(1).capitalize()

        return None

    def _looks_like_date(self, message: str) -> bool:
        """Very simple date detector for beginner code."""
        text = (message or "").strip()
        if not text:
            return False

        has_year = bool(re.search(r"\b(19|20)\d{2}\b", text))

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
