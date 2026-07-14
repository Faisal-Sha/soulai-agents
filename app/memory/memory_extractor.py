import json

from langchain_core.messages import HumanMessage, SystemMessage

from app.prompts.memory_prompt import MEMORY_EXTRACTION_PROMPT
from app.services.llm import llm


def extract_memory(user_message: str):

    response = llm.invoke(
        [
            SystemMessage(content=MEMORY_EXTRACTION_PROMPT),
            HumanMessage(content=user_message),
        ]
    )

    try:
        return json.loads(response.content)

    except Exception:
        return {
            "should_save": False
        }