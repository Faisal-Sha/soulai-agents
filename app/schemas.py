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

