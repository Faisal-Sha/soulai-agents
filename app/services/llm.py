from langchain_openai import ChatOpenAI
from app.config import OPENAI_API_KEY

# importing the tools 
from app.tools.knowledge import knowledge_search
from app.tools.user_context import get_user_context
from app.tools.memory import memory_search

llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model="gpt-4.1-mini",
    temperature=0.7,
    max_tokens=500
    )

tools = [
    knowledge_search,
    get_user_context,
    memory_search,
]

llm_with_tools = llm.bind_tools(tools)