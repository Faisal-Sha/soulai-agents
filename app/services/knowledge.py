from app.db.supabase import supabase
from app.services.embeddings import embed_query

RPC_MATCH_CHUNKS = "match_document_chunks"


class KnowledgeService:

    def search(self, query: str, match_count: int = 5, match_threshold: float = 0.3):
        query_vector = embed_query(query)

        response = supabase.rpc(
            RPC_MATCH_CHUNKS,
            {
                "query_embedding": query_vector,
                "match_count": match_count,
                "match_threshold": match_threshold,
            },
        ).execute()

        return response.data


knowledge_service = KnowledgeService()