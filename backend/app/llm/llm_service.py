import json

from app.llm.llm_client import LLMClient


class LLMService:

    def __init__(self):
        self.client = LLMClient()

    def generate_insights(self, dataset_info: dict):

        prompt = f"""
You are a senior business analyst.

Analyze the following dataset.

Dataset Information:

{dataset_info}

Return ONLY valid JSON.

Use EXACTLY this format:

{{
    "dataset_type": "",
    "business_summary": "",
    "recommended_charts": [],
    "possible_ml_tasks": []
}}

Do not write markdown.

Do not write explanations.

Return ONLY JSON.
"""

        response = self.client.chat(prompt)

        return json.loads(response)