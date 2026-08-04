from app.llm.llm_client import LLMClient


class ChatService:
    """
    Responsible for answering business questions
    about uploaded datasets.
    """

    def __init__(self):
        self.client = LLMClient()

    def answer_question(self, dataset_summary: dict, question: str):

        prompt = f"""
You are a senior Business Intelligence analyst.

Dataset Summary:

{dataset_summary}

User Question:

{question}

Rules:

- Answer ONLY using the provided dataset summary.
- If there is not enough information,
  clearly say that additional data is required.
- Keep answers concise.
"""

        return self.client.chat(prompt)