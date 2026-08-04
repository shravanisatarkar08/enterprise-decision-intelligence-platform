from fastapi import APIRouter, HTTPException

from app.schemas.chat_schema import ChatRequest, ChatResponse
from app.rag.data_store import data_store
from app.rag.rag_service import RAGService

router = APIRouter(
    prefix="/chat",
    tags=["Dataset Chat"]
)

rag_service = RAGService()


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):

    dataframe = data_store.get_dataset(request.dataset_id)

    if dataframe is None:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found."
        )

    answer = rag_service.answer_question(
        dataframe,
        request.question
    )

    return ChatResponse(
        answer=answer
    )