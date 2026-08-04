from app.llm.chat_service import ChatService
from app.rag.query_engine import QueryEngine


class RAGService:

    def __init__(self):
        self.chat_service = ChatService()

    def answer_question(self, dataframe, question: str):

        query_engine = QueryEngine(dataframe)

        # Step 1: Simple rule-based queries
        rule_answer = query_engine.execute_rule_based_query(question)

        if rule_answer:
            return rule_answer

        # Step 2: Smart Pandas queries
        smart_answer = query_engine.execute_smart_query(question)

        if smart_answer:
            return smart_answer

        # Step 3: LLM fallback
        dataset_summary = query_engine.get_dataset_summary()

        return self.chat_service.answer_question(
            dataset_summary,
            question
        )