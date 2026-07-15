from langchain_core.messages import (
    HumanMessage,
    AIMessage,
)

from app.db.supabase import supabase


class ChatHistoryService:

    def save_message(
        self,
        thread_id: str,
        user_id: str,
        role: str,
        content: str,
    ):

        supabase.rpc(
            "save_chat_message",
            {
                "p_thread_id": thread_id,
                "p_user_id": user_id,
                "p_role": role,
                "p_content": content,
            },
        ).execute()

    def get_history(
        self,
        thread_id: str,
        user_id: str,
    ):

        response = supabase.rpc(
            "get_chat_history",
            {
                "p_thread_id": thread_id,
                "p_user_id": user_id,
            },
        ).execute()

        return response.data or []

    def list_threads(self, user_id: str):

        response = supabase.rpc(
            "list_chat_threads",
            {
                "p_user_id": user_id,
            },
        ).execute()

        return response.data or []

    def to_langchain_messages(
        self,
        history: list,
    ):

        messages = []

        for item in history:

            if item["role"] == "user":

                messages.append(
                    HumanMessage(
                        content=item["content"]
                    )
                )

            elif item["role"] == "assistant":

                messages.append(
                    AIMessage(
                        content=item["content"]
                    )
                )

        return messages


chat_history_service = ChatHistoryService()
