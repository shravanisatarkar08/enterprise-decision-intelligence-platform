import os
import json

from groq import Groq


class LLMService:

    def __init__(self):
        self.client = Groq(
            api_key=os.getenv("GROQ_API_KEY")
        )

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

        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3
        )

        return json.loads(
            response.choices[0].message.content
        )