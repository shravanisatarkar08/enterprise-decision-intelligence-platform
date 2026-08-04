from pydantic import BaseModel


class ChatRequest(BaseModel):
    dataset_id: str
    question: str


class ChatResponse(BaseModel):
    answer: str