"""
Quick unit tests for memory JSON normalization (no OpenAI call).
"""

from app.memory.memory_extractor import _normalize_memories


class TestNormalizeMemories:

    def test_keeps_clear_relationship_fact(self):
        payload = {
            "should_save": True,
            "memories": [
                {
                    "category": "relationship",
                    "memory_key": "person_ali_relation",
                    "memory_value": "uncle",
                    "memory_text": "Ali is the user's uncle.",
                    "importance": 5,
                }
            ],
        }
        result = _normalize_memories(payload)
        assert len(result) == 1
        assert result[0]["memory_text"] == "Ali is the user's uncle."

    def test_drops_vague_meta_memory_text(self):
        payload = {
            "should_save": True,
            "memories": [
                {
                    "category": "personal",
                    "memory_key": "person_ali",
                    "memory_value": "Ali",
                    "memory_text": (
                        "User mentioned that the name of the person "
                        "in conversation is Ali."
                    ),
                    "importance": 3,
                }
            ],
        }
        result = _normalize_memories(payload)
        assert result == []

    def test_supports_old_single_object_format(self):
        payload = {
            "should_save": True,
            "category": "relationship",
            "memory_key": "person_ali_relation",
            "memory_value": "uncle",
            "memory_text": "Ali is the user's uncle.",
            "importance": 5,
        }
        result = _normalize_memories(payload)
        assert len(result) == 1
        assert result[0]["memory_key"] == "person_ali_relation"

    def test_multiple_facts_from_one_message(self):
        payload = {
            "should_save": True,
            "memories": [
                {
                    "category": "relationship",
                    "memory_key": "person_ali_relation",
                    "memory_value": "uncle",
                    "memory_text": "Ali is the user's uncle.",
                    "importance": 5,
                },
                {
                    "category": "relationship",
                    "memory_key": "person_ali_dob",
                    "memory_value": "11 July 1998",
                    "memory_text": "Ali (user's uncle) was born on 11 July 1998.",
                    "importance": 4,
                },
            ],
        }
        result = _normalize_memories(payload)
        assert len(result) == 2
