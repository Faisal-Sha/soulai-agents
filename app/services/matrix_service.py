"""
Matrix Service
==============

Beginner flow:

  PERSONAL (this user)
    DOB → calculate → save to saved_matrices → return JSON

  FRIEND / OTHER PERSON
    DOB → calculate → save facts to long-term memory → return JSON
    (never write friend matrices into saved_matrices)

Memory keys for a friend named Sarah:
  person_sarah_relation  → "friend"
  person_sarah_dob       → "1998-07-11"
  person_sarah_matrix    → compact matrix summary / JSON
"""

from __future__ import annotations

import json
import re

from app.db.supabase import supabase
from app.destiny_matrix import calculate_matrix, parse_dob
from app.services.memory_service import memory_service


def _slug_name(name: str) -> str:
    """Turn 'Sarah' / 'Mary Jane' into a stable memory key piece."""
    cleaned = re.sub(r"[^a-z0-9]+", "_", (name or "").strip().lower())
    return cleaned.strip("_") or "friend"


def _birth_date_iso(dob: dict) -> str:
    return f"{dob['year']:04d}-{dob['month']:02d}-{dob['day']:02d}"


def _matrix_summary(matrix: dict) -> str:
    """Short readable line for memory_value / memory_text."""
    keys = ("center", "top", "left", "right", "bottom", "money", "love")
    parts = [f"{key}={matrix[key]}" for key in keys if key in matrix]
    return ", ".join(parts)


class MatrixService:
    """Calculate a Destiny Matrix and store it in the right place."""

    def calculate(self, date_of_birth: str) -> dict:
        """
        Run the calculator only (no database / memory write).

        Returns:
          {
            "date_of_birth": {"day": 17, "month": 1, "year": 1993},
            "matrix": { "center": 8, "money": 12, ... }
          }
        """
        dob = parse_dob(date_of_birth)
        return {
            "date_of_birth": {
                "day": dob.day,
                "month": dob.month,
                "year": dob.year,
            },
            "matrix": calculate_matrix(dob),
        }

    def save_personal(
        self,
        *,
        user_id: str,
        birth_date: str,
        matrix_data: dict,
    ) -> dict:
        """Save ONLY this authenticated user's matrix into saved_matrices."""
        response = supabase.rpc(
            "save_matrix",
            {
                "p_user_id": user_id,
                "p_title": "My Destiny Matrix",
                "p_matrix_type": "personal",
                "p_birth_date": birth_date,
                "p_matrix_data": matrix_data,
                "p_birth_date_partner": None,
            },
        ).execute()
        return response.data or {}

    def save_friend_to_memory(
        self,
        *,
        user_id: str,
        person_name: str,
        birth_date: str,
        matrix: dict,
    ) -> list[dict]:
        """
        Remember a friend in long-term memory (not saved_matrices).

        Example for Sarah:
          person_sarah_relation, person_sarah_dob, person_sarah_matrix
        """
        name = (person_name or "").strip() or "Friend"
        slug = _slug_name(name)
        summary = _matrix_summary(matrix)
        matrix_json = json.dumps(matrix, separators=(",", ":"))

        facts = [
            {
                "category": "relationship",
                "key": f"person_{slug}_relation",
                "value": "friend",
                "memory_text": f"{name} is the user's friend.",
                "importance": 5,
            },
            {
                "category": "relationship",
                "key": f"person_{slug}_dob",
                "value": birth_date,
                "memory_text": (
                    f"{name} (user's friend) was born on {birth_date}."
                ),
                "importance": 5,
            },
            {
                "category": "relationship",
                "key": f"person_{slug}_matrix",
                "value": matrix_json,
                "memory_text": (
                    f"{name} (user's friend) Destiny Matrix: {summary}."
                ),
                "importance": 4,
            },
        ]

        saved_keys: list[dict] = []
        for fact in facts:
            memory_service.save_memory(
                user_id=user_id,
                category=fact["category"],
                key=fact["key"],
                value=fact["value"],
                memory_text=fact["memory_text"],
                importance=fact["importance"],
            )
            saved_keys.append(
                {
                    "memory_key": fact["key"],
                    "memory_text": fact["memory_text"],
                }
            )

        return saved_keys

    def calculate_and_store(
        self,
        *,
        user_id: str,
        date_of_birth: str,
        person_name: str = "",
        matrix_type: str = "friend",
    ) -> dict:
        """
        Full path used by the agent tool:

          personal → calculate + saved_matrices
          friend   → calculate + long-term memory
        """
        result = self.calculate(date_of_birth)
        birth_date = _birth_date_iso(result["date_of_birth"])

        clean_type = (matrix_type or "friend").strip().lower()
        if clean_type not in ("personal", "friend"):
            clean_type = "friend"

        name = (person_name or "").strip()

        if clean_type == "personal":
            saved = self.save_personal(
                user_id=user_id,
                birth_date=birth_date,
                matrix_data=result["matrix"],
            )
            return {
                "person_name": None,
                "matrix_type": "personal",
                "storage": "saved_matrices",
                "title": "My Destiny Matrix",
                "date_of_birth": result["date_of_birth"],
                "matrix": result["matrix"],
                "saved": True,
                "saved_record": saved,
            }

        memories = self.save_friend_to_memory(
            user_id=user_id,
            person_name=name,
            birth_date=birth_date,
            matrix=result["matrix"],
        )
        return {
            "person_name": name or None,
            "matrix_type": "friend",
            "storage": "memory",
            "title": (
                f"{name}'s Destiny Matrix" if name else "Destiny Matrix"
            ),
            "date_of_birth": result["date_of_birth"],
            "matrix": result["matrix"],
            "saved": True,
            "saved_memories": memories,
        }


matrix_service = MatrixService()
