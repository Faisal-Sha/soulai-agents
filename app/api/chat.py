from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage

from app.graph.graph import graph
from app.schemas import ChatRequest, ChatResponse
from app.services.language import detect_user_language

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        user_language = detect_user_language(request.message)

        result = graph.invoke(
            {
                "messages": [
                    HumanMessage(content=request.message)
                ],
                "user_language": user_language,
            }
        )

        ai_message = result["messages"][-1]
        answer = ai_message.content
        if not answer:
            answer = "I could not generate a response. Please try again."

        return ChatResponse(
            answer=answer,
            sources=[],
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )