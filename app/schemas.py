from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class KnowledgeSource(BaseModel):
    id: str | None = None
    document_id: str | None = None
    chunk_index: int | None = None
    similarity: float | None = None
    summary: str | None = None
    content: str | None = None
    metadata: dict | None = None
    token_count: int | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[KnowledgeSource] = []

