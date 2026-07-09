from app.db.supabase import supabase

RPC_NAME = "get_user_context"

class UserContextService:
    def get_context(self, user_id: str):
        if not user_id:
            return {"error": "User id is required"}

        response = supabase.rpc(
            RPC_NAME,
            {
                "p_user_id": user_id,
            },
        ).execute()

        return response.data or {"error": "No user context found"}

user_context_service = UserContextService()