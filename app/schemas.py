from datetime import datetime

from pydantic import BaseModel


# user message schema
class ChatRequest(BaseModel):
    message: str
    thread_id: str
    user_id: str


# schema of supabase knowledge source (document_chunks)
class KnowledgeSource(BaseModel):
    id: str | None = None
    document_id: str | None = None
    chunk_index: int | None = None
    similarity: float | None = None
    summary: str | None = None
    content: str | None = None
    metadata: dict | None = None
    token_count: int | None = None


# system response schema
class ChatResponse(BaseModel):
    answer: str
    sources: list[KnowledgeSource] = []

    # "complete" = normal finished answer
    # "waiting"  = we asked a follow-up and stored conversation_context
    status: str = "complete"

    # Optional snapshot of pending slots (useful for debugging / UI)
    # Example: {"intent": "friend_matrix", "slots": {"friend_name": "Asim", "friend_dob": null}}
    pending: dict | None = None


class ChatThreadSummary(BaseModel):
    thread_id: str
    preview: str | None = None
    message_count: int = 0
    updated_at: datetime | None = None


class ChatHistoryMessage(BaseModel):
    id: str | None = None
    thread_id: str
    user_id: str
    role: str
    content: str
    created_at: datetime | None = None

