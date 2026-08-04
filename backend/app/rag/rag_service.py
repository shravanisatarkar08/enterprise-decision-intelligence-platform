import json

from app.llm.chat_service import ChatService
from app.rag.query_engine import QueryEngine


class RAGService:

    def __init__(self):
        self.chat_service = ChatService()

    def answer_question(self, dataframe, question: str):

        query_engine = QueryEngine(dataframe)

        dataset_summary = query_engine.get_dataset_summary()
        return self.chat_service.answer_question(
        dataset_summary,
        question
    )
