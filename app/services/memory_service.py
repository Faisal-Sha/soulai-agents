from app.db.supabase import supabase


class MemoryService:

    def save_memory(
        self,
        user_id: str,
        category: str,
        key: str,
        value: str,
        memory_text: str,
        importance: int = 3,
    ):

        supabase.rpc(
            "save_memory",
            {
                "p_user_id": user_id,
                "p_category": category,
                "p_memory_key": key,
                "p_memory_value": value,
                "p_memory_text": memory_text,
                "p_importance": importance,
            },
        ).execute()

    def search_memories(
        self,
        user_id: str,
    ):

        response = supabase.rpc(
            "search_memories",
            {
                "p_user_id": user_id,
            },
        ).execute()

        return response.data or []


memory_service = MemoryService()