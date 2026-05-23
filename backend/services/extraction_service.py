import os
import json
from google import genai
from google.genai import types
from langsmith import traceable
from models import CallExtraction

class ExtractionService:
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None
            print("[WARN] GEMINI_API_KEY not found. ExtractionService will fail.")

    @traceable(name="transcript-full-extraction", run_type="chain")
    def extract_structured_data(self, transcript_text: str) -> CallExtraction:
        if not self.client:
            raise ValueError("GEMINI_API_KEY is not configured.")

        system_instruction = """You are an expert call analytics AI. 
Analyze the provided customer service transcript and extract highly accurate structured insights.
Pay close attention to root causes, escalation signals, customer sentiment changes, and the agent's performance."""

        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"Please analyze this transcript:\n\n{transcript_text}",
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=CallExtraction,
                    temperature=0.1,
                ),
            )
            
            # response.text is guaranteed to match the Pydantic schema
            data = json.loads(response.text)
            return CallExtraction(**data)
            
        except Exception as e:
            print(f"[ERROR] Failed to extract structured data: {e}")
            raise
