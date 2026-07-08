from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage

from app.graph.graph import graph
from app.schemas import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        result = graph.invoke(
            {
                "messages": [
                    HumanMessage(content=request.message)
                ]
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