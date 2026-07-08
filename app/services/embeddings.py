from langchain_openai import OpenAIEmbeddings
from app.config import OPENAI_API_KEY

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=OPENAI_API_KEY,
)


def embed_query(text: str):

    return embeddings.embed_query(text)